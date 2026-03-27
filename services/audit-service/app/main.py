from datetime import datetime

from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session

from shared.app.config import settings
from shared.app.db import get_db
from shared.app.logging_utils import configure_logging, log_kv
from shared.app.models import AuditEvent
from shared.app.schemas import AuditEventOut, HealthResponse, RiskCheckResult
from shared.app.kafka import start_consumer, stop_consumers
from shared.app.topics import RISK_ORDER_APPROVED, RISK_ORDER_APPROVED_LEGACY, dlq_topic

app = FastAPI(title='Audit Service')
logger = configure_logging('audit-service')


async def handle_approved_event(event: RiskCheckResult):
    log_kv(logger, 'AuditService', 'migration_compat_event_seen', order_id=event.order_id, approved=event.approved)


@app.on_event('startup')
async def startup():
    await start_consumer([RISK_ORDER_APPROVED, RISK_ORDER_APPROVED_LEGACY], 'audit-approved-compat', RiskCheckResult, handle_approved_event)


@app.on_event('shutdown')
async def shutdown():
    await stop_consumers()


@app.get('/health', response_model=HealthResponse)
def health():
    return HealthResponse(status='ok', service=settings.service_name)


@app.get('/audit/events', response_model=list[AuditEventOut])
def list_events(
    topic: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(AuditEvent)
    if topic:
        query = query.filter(AuditEvent.topic == topic)
    if since:
        query = query.filter(AuditEvent.created_at >= since)
    rows = query.order_by(AuditEvent.created_at.asc()).all()
    log_kv(logger, 'AuditService', 'list_events', count=len(rows), topic=topic or 'all')
    return [
        AuditEventOut(id=row.id, topic=row.topic, event_key=row.event_key, payload=row.payload, created_at=row.created_at)
        for row in rows
    ]


@app.get('/audit/dlq/{topic}')
def list_dlq_messages(topic: str, since: datetime | None = Query(default=None), db: Session = Depends(get_db)):
    target_topic = dlq_topic(topic)
    query = db.query(AuditEvent).filter(AuditEvent.topic == target_topic)
    if since:
        query = query.filter(AuditEvent.created_at >= since)
    rows = query.order_by(AuditEvent.created_at.asc()).all()
    log_kv(logger, 'AuditService', 'list_dlq', topic=target_topic, count=len(rows))
    return [
        {'id': str(row.id), 'topic': row.topic, 'payload': row.payload, 'created_at': row.created_at.isoformat()}
        for row in rows
    ]


# TODO(Phase2.2+): remove legacy compatibility subscription for risk.order.aproved.v1 after migration window.
