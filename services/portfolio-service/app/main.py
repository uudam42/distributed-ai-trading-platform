from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from shared.app.audit import record_audit
from shared.app.config import settings
from shared.app.db import SessionLocal, get_db
from shared.app.deps import get_current_claims
from shared.app.idempotency import already_processed, mark_processed
from shared.app.kafka import start_consumer, stop_consumers
from shared.app.logging_utils import configure_logging, log_kv
from shared.app.models import Account, Position
from shared.app.schemas import HealthResponse, PositionOut, TradeEvent
from shared.app.topics import TRADES_EXECUTED

app = FastAPI(title='Portfolio Service')
logger = configure_logging('portfolio-service')


async def handle_trade(event: TradeEvent):
    db = SessionLocal()
    try:
        if already_processed(db, 'portfolio-service', str(event.trade_id)):
            log_kv(logger, 'PortfolioService', 'idempotent_skip', trade_id=event.trade_id)
            return
        qty = Decimal(str(event.quantity))
        price = Decimal(str(event.price))
        notional = qty * price

        buy_account = db.query(Account).filter(Account.id == event.buy_account_id).first()
        sell_account = db.query(Account).filter(Account.id == event.sell_account_id).first()

        if buy_account:
            buy_account.cash_balance = Decimal(str(buy_account.cash_balance)) - notional
        if sell_account:
            sell_account.cash_balance = Decimal(str(sell_account.cash_balance)) + notional

        update_position(db, str(event.buy_account_id), event.instrument_id, qty, price)
        update_position(db, str(event.sell_account_id), event.instrument_id, -qty, price)
        db.commit()
        mark_processed(db, 'portfolio-service', str(event.trade_id), 'portfolio_trade_applied')
        record_audit(db, 'portfolio.position.updated.v1', event.model_dump(mode='json'), str(event.trade_id))
        log_kv(logger, 'PortfolioService', 'updated', buy_account=event.buy_account_id, sell_account=event.sell_account_id, symbol=event.instrument_id, qty=event.quantity, price=event.price)
    finally:
        db.close()


def update_position(db: Session, account_id: str, instrument_id: str, delta_qty: Decimal, price: Decimal):
    pos = db.query(Position).filter(Position.account_id == account_id, Position.instrument_id == instrument_id).first()
    if not pos:
        pos = Position(account_id=account_id, instrument_id=instrument_id, quantity=0, avg_cost=0, realized_pnl=0, updated_at=datetime.utcnow())
        db.add(pos)
        db.flush()
    current_qty = Decimal(str(pos.quantity))
    new_qty = current_qty + delta_qty
    if delta_qty > 0:
        total_cost = (current_qty * Decimal(str(pos.avg_cost))) + (delta_qty * price)
        pos.quantity = new_qty
        pos.avg_cost = 0 if new_qty == 0 else total_cost / new_qty
    else:
        pos.quantity = new_qty
    pos.updated_at = datetime.utcnow()


@app.on_event('startup')
async def startup():
    await start_consumer(TRADES_EXECUTED, 'portfolio-service', TradeEvent, handle_trade)


@app.on_event('shutdown')
async def shutdown():
    await stop_consumers()


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


@app.get('/portfolio/{account_id}', response_model=list[PositionOut])
def get_portfolio(account_id: str, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    if account_id != claims.get('account_id'):
        return []
    rows = db.query(Position).filter(Position.account_id == account_id).all()
    return [
        PositionOut(
            account_id=row.account_id,
            instrument_id=row.instrument_id,
            quantity=float(row.quantity),
            avg_cost=float(row.avg_cost),
            realized_pnl=float(row.realized_pnl),
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@app.get('/accounts/{account_id}')
def get_account(account_id: str, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    if account_id != claims.get('account_id'):
        return {}
    account = db.query(Account).filter(Account.id == account_id).first()
    return {
        'id': str(account.id),
        'user_id': str(account.user_id),
        'name': account.name,
        'cash_balance': float(account.cash_balance),
    }


# TODO(Phase3): Add Redis-backed hot portfolio cache and realized/unrealized PnL read models.
