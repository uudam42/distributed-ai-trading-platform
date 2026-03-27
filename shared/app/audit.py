from sqlalchemy.orm import Session

from .models import AuditEvent


def record_audit(db: Session, topic: str, payload: dict, event_key: str | None = None):
    db.add(AuditEvent(topic=topic, payload=payload, event_key=event_key))
    db.commit()
