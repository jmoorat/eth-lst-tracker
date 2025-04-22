from datetime import datetime
from enum import Enum

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud
import models
from crud import QueryableTimeBucket
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="ETH LST tracker API",
    summary="API to track prices and premiums of various Ethereum Liquid Staking Tokens (LST).",
    docs_url=None,
    redoc_url="/docs",
)


class PriceHistoryResolutionRequest(str, Enum):
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


class FullPriceResponse(BaseModel):
    timestamp: datetime
    token_name: str
    network: str
    is_primary_market: bool
    price_eth: float
    premium_percentage: float


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/prices")
def get_last_prices(db: Session = Depends(get_db)) -> list[FullPriceResponse]:
    last_prices = crud.get_last_prices(db)
    return [FullPriceResponse(**r) for r in last_prices]


@app.get("/prices/{token_name}/history")
def get_price_history(
    token_name: str,
    network: str = "ethereum",
    primary_market: bool = False,
    resolution: PriceHistoryResolutionRequest = PriceHistoryResolutionRequest.ONE_DAY,
    db: Session = Depends(get_db),
) -> PriceResponse:
    if primary_market and network != "ethereum":
        raise HTTPException(
            status_code=400, detail="Primary market is only available on Ethereum"
        )
    result = crud.get_price_history(
        db,
        token_name,
        network,
        primary_market,
        resolution_request_to_time_bucket[resolution],
    )
    response: PriceResponse = PriceResponse(
        token_name=token_name,
        network=network,
        is_primary_market=primary_market,
        prices=[
            PriceHistoryResponse(
                timestamp=r["time_bucket"],
                price_eth=r["price_eth"],
                premium_percentage=r["premium_percentage"],
            )
            for r in result
        ],
    )

    return response


@app.get("/prices/{token_name}/last")
def get_last_price(
    token_name: str,
    network: str = "ethereum",
    primary_market: bool = False,
    db: Session = Depends(get_db),
) -> FullPriceResponse:
    last_price = crud.get_last_price(db, token_name, network, primary_market)

    if primary_market and network != "ethereum":
        raise HTTPException(
            status_code=400, detail="Primary market is only available on Ethereum"
        )

    if not last_price:
        raise HTTPException(status_code=404, detail="Item not found")

    return FullPriceResponse(
        token_name=token_name,
        network=network,
        is_primary_market=primary_market,
        **last_price,
    )
