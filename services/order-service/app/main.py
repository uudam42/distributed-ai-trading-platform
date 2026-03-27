from datetime import datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from shared.app.audit import record_audit
from shared.app.config import settings
from shared.app.db import get_db
from shared.app.deps import get_current_claims
from shared.app.kafka import publish, start_producer, stop_producer
from shared.app.logging_utils import configure_logging, log_kv
from shared.app.models import Order
from shared.app.schemas import CreateOrderRequest, HealthResponse, OrderEvent, OrderOut, RiskCheckResult
from shared.app.topics import ORDERS_RECEIVED

app = FastAPI(title='Order Service')
logger = configure_logging('order-service')


@app.on_event('startup')
async def startup():
    await start_producer()


@app.on_event('shutdown')
async def shutdown():
    await stop_producer()


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


@app.post('/orders', response_model=OrderOut, status_code=202)
async def create_order(request: CreateOrderRequest, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    if str(request.account_id) != claims.get('account_id'):
        raise HTTPException(status_code=403, detail='Account mismatch')
    order = Order(
        account_id=request.account_id,
        instrument_id=request.instrument_id,
        side=request.side,
        order_type=request.order_type,
        quantity=request.quantity,
        price=request.price,
        status='PENDING_RISK',
        source='api',
        updated_at=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    event = OrderEvent(
        event_id=uuid4(),
        order_id=order.id,
        account_id=order.account_id,
        instrument_id=order.instrument_id,
        side=order.side,
        quantity=float(order.quantity),
        price=float(order.price),
        status=order.status,
        timestamp=datetime.utcnow(),
    )
    payload = event.model_dump(mode='json')
    await publish(ORDERS_RECEIVED, payload, key=str(order.account_id))
    record_audit(db, ORDERS_RECEIVED, payload, str(order.id))
    log_kv(logger, 'OrderService', 'received_order', user=claims.get('email'), symbol=order.instrument_id, side=order.side, qty=float(order.quantity), price=float(order.price), order_id=order.id)
    return OrderOut(
        id=order.id,
        account_id=order.account_id,
        instrument_id=order.instrument_id,
        side=order.side,
        order_type=order.order_type,
        quantity=float(order.quantity),
        price=float(order.price),
        status=order.status,
        source=order.source,
        created_at=order.created_at,
    )


@app.get('/orders', response_model=list[OrderOut])
def list_orders(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    rows = db.query(Order).filter(Order.account_id == claims.get('account_id')).order_by(Order.created_at.asc()).all()
    return [
        OrderOut(
            id=row.id,
            account_id=row.account_id,
            instrument_id=row.instrument_id,
            side=row.side,
            order_type=row.order_type,
            quantity=float(row.quantity),
            price=float(row.price) if row.price is not None else None,
            status=row.status,
            source=row.source,
            created_at=row.created_at,
        )
        for row in rows
    ]


@app.get('/orders/{order_id}', response_model=OrderOut)
def get_order(order_id: str, claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    row = db.query(Order).filter(Order.id == order_id, Order.account_id == claims.get('account_id')).first()
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    return OrderOut(
        id=row.id,
        account_id=row.account_id,
        instrument_id=row.instrument_id,
        side=row.side,
        order_type=row.order_type,
        quantity=float(row.quantity),
        price=float(row.price) if row.price is not None else None,
        status=row.status,
        source=row.source,
        created_at=row.created_at,
    )


@app.get('/orders/replay/{topic}')
async def replay_topic(topic: str):
    return {'status': 'available', 'topic': topic, 'note': 'Use Kafka offsets reset / consumer group replay for debugging in this phase.'}


# TODO(Phase2+): Add amend/cancel endpoints and outbox-based exactly-once publishing.
