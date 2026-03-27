from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base


class ProcessedEvent(Base):
    __tablename__ = 'processed_events'
    __table_args__ = (
        Index('ix_processed_events_service_event', 'service_name', 'event_id', unique=True),
        {'schema': 'audit'},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)


def already_processed(db: Session, service_name: str, event_id: str) -> bool:
    return db.query(ProcessedEvent).filter(
        ProcessedEvent.service_name == service_name,
        ProcessedEvent.event_id == event_id,
    ).first() is not None


def mark_processed(db: Session, service_name: str, event_id: str, event_type: str) -> None:
    db.add(ProcessedEvent(service_name=service_name, event_id=event_id, event_type=event_type))
    db.commit()
