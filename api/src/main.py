from enum import Enum

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import crud, models
from .crud import QueryableTimeBucket
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI()


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


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/prices")
def get_last_prices(db: Session = Depends(get_db)):
    last_prices = crud.get_last_prices(db)
    return last_prices


@app.get("/prices/{token_name}/history")
def get_price_history(
        token_name: str,
        network: str = "ethereum",
        primary_market: bool = False,
        resolution: PriceHistoryResolutionRequest = PriceHistoryResolutionRequest.ONE_DAY,
        db: Session = Depends(get_db)
):
    if primary_market and network != "ethereum":
        raise HTTPException(status_code=400, detail="Primary market is only available on Ethereum")
    result = crud.get_price_history(db, token_name, network, primary_market, resolution_request_to_time_bucket[resolution])

    return result


@app.get("/prices/{token_name}/last")
def get_last_price(
        token_name: str,
        network: str = "ethereum",
        primary_market: bool = False,
        db: Session = Depends(get_db)
):
    last_prices = crud.get_last_price(db, token_name, network, primary_market)

    if primary_market and network != "ethereum":
        raise HTTPException(status_code=400, detail="Primary market is only available on Ethereum")

    if not last_prices:
        raise HTTPException(status_code=404, detail="Item not found")

    return last_prices
