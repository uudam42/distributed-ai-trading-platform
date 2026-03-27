from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI
from sqlalchemy.orm import Session

from shared.app.audit import record_audit
from shared.app.config import settings
from shared.app.db import SessionLocal
from shared.app.idempotency import already_processed, mark_processed
from shared.app.kafka import publish, start_consumer, start_producer, stop_consumers, stop_producer
from shared.app.logging_utils import configure_logging, log_kv
from shared.app.models import Account, Order
from shared.app.schemas import HealthResponse, OrderEvent, RiskCheckResult
from shared.app.topics import ORDERS_ACCEPTED, ORDERS_RECEIVED, RISK_ORDER_APPROVED, RISK_ORDER_REJECTED

app = FastAPI(title='Risk Service')
logger = configure_logging('risk-service')


def evaluate_order(db: Session, event: OrderEvent) -> RiskCheckResult:
    account = db.query(Account).filter(Account.id == event.account_id).first()
    order = db.query(Order).filter(Order.id == event.order_id).first()
    approved = False
    reason = 'unknown'
    if account and order:
        notional = Decimal(str(event.quantity)) * Decimal(str(event.price))
        if event.side == 'BUY':
            approved = Decimal(str(account.cash_balance)) >= notional
            reason = 'approved' if approved else 'insufficient_cash'
        else:
            approved = True
            reason = 'approved'
        order.status = 'ACCEPTED' if approved else 'REJECTED'
        db.commit()
    return RiskCheckResult(
        event_id=uuid4(),
        order_id=event.order_id,
        approved=approved,
        reason=reason,
        account_id=event.account_id,
        instrument_id=event.instrument_id,
        side=event.side,
        quantity=event.quantity,
        price=event.price,
        timestamp=datetime.utcnow(),
        retry_count=event.retry_count,
    )


async def handle_order(event: OrderEvent):
    db = SessionLocal()
    try:
        if already_processed(db, 'risk-service', str(event.event_id)):
            log_kv(logger, 'RiskService', 'idempotent_skip', event_id=event.event_id)
            return
        result = evaluate_order(db, event)
        mark_processed(db, 'risk-service', str(event.event_id), 'order_risk_evaluated')
        topic = RISK_ORDER_APPROVED if result.approved else RISK_ORDER_REJECTED
        payload = result.model_dump(mode='json')
        await publish(topic, payload, key=str(result.account_id))
        if result.approved:
            accepted = event.model_dump(mode='json')
            accepted['status'] = 'ACCEPTED'
            await publish(ORDERS_ACCEPTED, accepted, key=str(result.account_id))
            log_kv(logger, 'RiskService', 'approved', order_id=result.order_id, symbol=result.instrument_id, qty=result.quantity, price=result.price)
        else:
            log_kv(logger, 'RiskService', 'rejected', order_id=result.order_id, reason=result.reason)
        record_audit(db, topic, payload, str(result.order_id))
    finally:
        db.close()


@app.on_event('startup')
async def startup():
    await start_producer()
    await start_consumer(ORDERS_RECEIVED, 'risk-service', OrderEvent, handle_order)


@app.on_event('shutdown')
async def shutdown():
    await stop_consumers()
    await stop_producer()


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


# TODO(Phase2.2+): remove compatibility handling for legacy topic risk.order.aproved.v1 after migration window.
# TODO(Phase3): Add richer cross-position risk, limits, and Redis hot-state exposure cache.
