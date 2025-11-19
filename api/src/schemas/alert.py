import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, EmailStr


class AlertMetric(StrEnum):
    price_eth = "price_eth"
    premium = "premium"


class AlertCondition(StrEnum):
    lt = "lt"
    lte = "lte"
    gt = "gt"
    gte = "gte"
    eq = "eq"


class AlertType(StrEnum):
    ONE_OFF = "one_off"
    # RECURRENT = "recurrent" -- Future implementation


class AlertStatus(StrEnum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AlertCreate(BaseModel):
    email: EmailStr
    token_name: str
    network: str
    is_primary_market: bool
    metric: AlertMetric
    condition: AlertCondition
    threshold: float
    type: AlertType
    expires_at: Optional[datetime] = None


class Alert(BaseModel):
    id: uuid.UUID
    email: EmailStr
    token_name: str
    network: str
    is_primary_market: bool
    metric: AlertMetric
    condition: AlertCondition
    threshold: float
    type: AlertType
    status: AlertStatus
    trigger_count: int = 0
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None

    class Config:
        orm_mode = True
