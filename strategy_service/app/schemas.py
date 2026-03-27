from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel


class BacktestResult(BaseModel):
    event_id: UUID = uuid4()
    strategy_name: str
    dataset: str
    pnl: float
    number_of_trades: int
    fill_ratio: float
    inventory_exposure: float
    report_path: str
    timestamp: datetime
