from collections import defaultdict, deque
from dataclasses import dataclass
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
from shared.app.models import Order, Trade
from shared.app.schemas import HealthResponse, OrderEvent, TradeEvent
from shared.app.topics import ORDERS_ACCEPTED, TRADES_EXECUTED

app = FastAPI(title='Matching Engine')
logger = configure_logging('matching-engine')


@dataclass
class BookOrder:
    order_id: str
    account_id: str
    instrument_id: str
    side: str
    quantity: Decimal
    price: Decimal
    timestamp: str


class OrderBook:
    def __init__(self):
        self.buys = defaultdict(deque)
        self.sells = defaultdict(deque)

    def add(self, order: BookOrder):
        book = self.buys if order.side == 'BUY' else self.sells
        book[order.instrument_id].append(order)

    def best_buy(self, instrument_id: str):
        orders = sorted(self.buys[instrument_id], key=lambda o: (-o.price, o.timestamp))
        return orders[0] if orders else None

    def best_sell(self, instrument_id: str):
        orders = sorted(self.sells[instrument_id], key=lambda o: (o.price, o.timestamp))
        return orders[0] if orders else None

    def remove(self, order: BookOrder):
        book = self.buys if order.side == 'BUY' else self.sells
        queue = book[order.instrument_id]
        for i, existing in enumerate(queue):
            if existing.order_id == order.order_id:
                del queue[i]
                break


order_book = OrderBook()


async def handle_order(event: OrderEvent):
    db = SessionLocal()
    try:
        if already_processed(db, 'matching-engine-order', str(event.event_id)):
            log_kv(logger, 'MatchingEngine', 'idempotent_skip', event_id=event.event_id)
            return
        incoming = BookOrder(
            order_id=str(event.order_id),
            account_id=str(event.account_id),
            instrument_id=event.instrument_id,
            side=event.side,
            quantity=Decimal(str(event.quantity)),
            price=Decimal(str(event.price)),
            timestamp=event.timestamp.isoformat(),
        )
        mark_processed(db, 'matching-engine-order', str(event.event_id), 'accepted_order_seen')
        order_book.add(incoming)
        log_kv(logger, 'MatchingEngine', 'booked', order_id=incoming.order_id, side=incoming.side, symbol=incoming.instrument_id, qty=float(incoming.quantity), price=float(incoming.price))
        await match_loop(incoming.instrument_id, db)
    finally:
        db.close()


async def match_loop(instrument_id: str, db: Session):
    while True:
        buy = order_book.best_buy(instrument_id)
        sell = order_book.best_sell(instrument_id)
        if not buy or not sell or buy.price < sell.price:
            break
        trade_qty = min(buy.quantity, sell.quantity)
        trade_price = sell.price if sell.timestamp <= buy.timestamp else buy.price
        trade = TradeEvent(
            event_id=uuid4(),
            trade_id=uuid4(),
            buy_order_id=buy.order_id,
            sell_order_id=sell.order_id,
            buy_account_id=buy.account_id,
            sell_account_id=sell.account_id,
            instrument_id=instrument_id,
            quantity=float(trade_qty),
            price=float(trade_price),
            timestamp=datetime.utcnow(),
        )
        if already_processed(db, 'matching-engine-trade', str(trade.trade_id)):
            log_kv(logger, 'MatchingEngine', 'idempotent_skip', trade_id=trade.trade_id)
            break
        db.add(Trade(
            id=trade.trade_id,
            buy_order_id=trade.buy_order_id,
            sell_order_id=trade.sell_order_id,
            instrument_id=instrument_id,
            quantity=float(trade_qty),
            price=float(trade_price),
        ))
        buy_row = db.query(Order).filter(Order.id == buy.order_id).first()
        sell_row = db.query(Order).filter(Order.id == sell.order_id).first()
        if buy_row:
            buy_row.status = 'FILLED' if buy.quantity == trade_qty else 'PARTIALLY_FILLED'
        if sell_row:
            sell_row.status = 'FILLED' if sell.quantity == trade_qty else 'PARTIALLY_FILLED'
        db.commit()
        mark_processed(db, 'matching-engine-trade', str(trade.trade_id), 'trade_executed')
        payload = trade.model_dump(mode='json')
        await publish(TRADES_EXECUTED, payload, key=instrument_id)
        record_audit(db, TRADES_EXECUTED, payload, str(trade.trade_id))
        log_kv(logger, 'MatchingEngine', 'matched', trade_id=trade.trade_id, symbol=instrument_id, price=float(trade_price), qty=float(trade_qty))
        buy.quantity -= trade_qty
        sell.quantity -= trade_qty
        if buy.quantity == 0:
            order_book.remove(buy)
        if sell.quantity == 0:
            order_book.remove(sell)


@app.on_event('startup')
async def startup():
    await start_producer()
    await start_consumer(ORDERS_ACCEPTED, 'matching-engine', OrderEvent, handle_order)


@app.on_event('shutdown')
async def shutdown():
    await stop_consumers()
    await stop_producer()


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


# TODO(Phase3): Replace Python order book with lower-latency engine while keeping event contract stable.
