import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, EmailStr


class LstPrice(BaseModel):
    timestamp: str
    token_name: str
    network: str
    price_eth: float
    price_usd: float
    is_primary_market: bool
    premium: float

    # transform premium to percentage
    @property
    def premium_percentage(self):
        return self.premium * 100


class QueryableTimeBucket(StrEnum):
    FIVE_MINUTES = "5 minutes"
    ONE_HOUR = "1 hour"
    ONE_DAY = "1 day"
    ONE_WEEK = "1 week"
    ONE_MONTH = "1 month"


interval_limits_per_time_buckets = {
    QueryableTimeBucket.FIVE_MINUTES: "1 day",
    QueryableTimeBucket.ONE_HOUR: "1 week",
    QueryableTimeBucket.ONE_DAY: "6 months",
    QueryableTimeBucket.ONE_WEEK: "1 year",
    QueryableTimeBucket.ONE_MONTH: "5 years",
}


class PriceHistoryResolutionRequest(StrEnum):
    FIVE_MINUTES = "5min"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"


resolution_request_to_time_bucket = {
    PriceHistoryResolutionRequest.FIVE_MINUTES: QueryableTimeBucket.FIVE_MINUTES,
    PriceHistoryResolutionRequest.ONE_HOUR: QueryableTimeBucket.ONE_HOUR,
    PriceHistoryResolutionRequest.ONE_DAY: QueryableTimeBucket.ONE_DAY,
    PriceHistoryResolutionRequest.ONE_WEEK: QueryableTimeBucket.ONE_WEEK,
    PriceHistoryResolutionRequest.ONE_MONTH: QueryableTimeBucket.ONE_MONTH,
}


class PriceHistoryResponse(BaseModel):
    timestamp: datetime
    price_eth: float
    premium_percentage: float


class PriceResponse(BaseModel):
    token_name: str
    network: str
    is_primary_market: bool
    prices: list[PriceHistoryResponse]


class PriceHistoryStats(BaseModel):
    first: float
    min: float
    avg: float
    max: float
    last: float


class AdvancedPriceHistoryResponse(BaseModel):
    timestamp: datetime
    price_eth: PriceHistoryStats
    premium_percentage: PriceHistoryStats


class AdvancedPriceResponse(BaseModel):
    token_name: str
    network: str
    is_primary_market: bool
    prices: list[AdvancedPriceHistoryResponse]


class FullPriceResponse(BaseModel):
    timestamp: datetime
    token_name: str
    network: str
    is_primary_market: bool
    price_eth: float
    premium_percentage: float


class TokenNetworksResponse(BaseModel):
    token_name: str
    networks: list[str]


class TokenNetworkResponse(BaseModel):
    token_name: str
    network: str
    is_primary_market: bool


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
