from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    event_id: UUID = uuid4()
    analysis_type: Literal['risk_explanation', 'strategy_summary', 'portfolio_qa']
    payload: dict
    timestamp: datetime | None = None


class AnalyzeResult(BaseModel):
    event_id: UUID
    analysis_type: str
    result: dict
    timestamp: datetime
