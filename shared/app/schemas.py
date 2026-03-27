from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_id: UUID
    account_id: UUID


class UserOut(BaseModel):
    id: UUID
    email: EmailStr


class AccountOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    cash_balance: float


class CreateOrderRequest(BaseModel):
    account_id: UUID
    instrument_id: str
    side: Literal['BUY', 'SELL']
    order_type: Literal['LIMIT']
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)


class OrderOut(BaseModel):
    id: UUID
    account_id: UUID
    instrument_id: str
    side: str
    order_type: str
    quantity: float
    price: float | None
    status: str
    source: str
    created_at: datetime


class RiskCheckRequest(BaseModel):
    order_id: UUID
    account_id: UUID
    instrument_id: str
    side: Literal['BUY', 'SELL']
    quantity: float
    price: float
    status: str
    timestamp: datetime


class RiskCheckResult(BaseModel):
    event_id: UUID
    order_id: UUID
    approved: bool
    reason: str
    account_id: UUID
    instrument_id: str
    side: Literal['BUY', 'SELL']
    quantity: float
    price: float
    timestamp: datetime
    retry_count: int = 0


class OrderEvent(BaseModel):
    event_id: UUID
    order_id: UUID
    account_id: UUID
    instrument_id: str
    side: Literal['BUY', 'SELL']
    quantity: float
    price: float
    status: str
    timestamp: datetime
    retry_count: int = 0


class TradeEvent(BaseModel):
    event_id: UUID
    trade_id: UUID
    buy_order_id: UUID
    sell_order_id: UUID
    buy_account_id: UUID
    sell_account_id: UUID
    instrument_id: str
    quantity: float
    price: float
    timestamp: datetime
    retry_count: int = 0


class PositionOut(BaseModel):
    account_id: UUID
    instrument_id: str
    quantity: float
    avg_cost: float
    realized_pnl: float
    updated_at: datetime


class AuditEventOut(BaseModel):
    id: UUID
    topic: str
    event_key: str | None
    payload: dict
    created_at: datetime
