from datetime import datetime
from enum import Enum

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud
import models
import schemas
from schemas import (
    AdvancedPriceHistoryResponse,
    AdvancedPriceResponse,
    FullPriceResponse,
    PriceHistoryResolutionRequest,
    PriceHistoryResponse,
    PriceResponse,
    PriceHistoryStats,
    TokenNetworkResponse,
    resolution_request_to_time_bucket
)
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="ETH LST tracker API",
    summary="API to track prices and premiums of various Ethereum Liquid Staking Tokens (LST).",
    docs_url=None,
    redoc_url="/docs",
)




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
        False,
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


@app.get("/prices/{token_name}/history/advanced")
def get_advanced_price_history(
    token_name: str,
    network: str = "ethereum",
    primary_market: bool = False,
    resolution: PriceHistoryResolutionRequest = PriceHistoryResolutionRequest.ONE_DAY,
    db: Session = Depends(get_db),
) -> AdvancedPriceResponse:
    if primary_market and network != "ethereum":
        raise HTTPException(
            status_code=400, detail="Primary market is only available on Ethereum"
        )

    result = crud.get_price_history(
        db,
        token_name,
        network,
        primary_market,
        True,
        resolution_request_to_time_bucket[resolution],
    )

    response: AdvancedPriceResponse = AdvancedPriceResponse(
        token_name=token_name,
        network=network,
        is_primary_market=primary_market,
        prices=[
            AdvancedPriceHistoryResponse(
                timestamp=r["time_bucket"],
                price_eth=PriceHistoryStats(
                    min=r["min_price_eth"],
                    max=r["max_price_eth"],
                    avg=r["avg_price_eth"],
                    first=r["first_price_eth"],
                    last=r["last_price_eth"],
                ),
                premium_percentage=PriceHistoryStats(
                    min=r["min_premium_percentage"],
                    max=r["max_premium_percentage"],
                    avg=r["avg_premium_percentage"],
                    first=r["first_premium_percentage"],
                    last=r["last_premium_percentage"],
                ),
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


@app.get("/tokens")
def get_available_tokens(db: Session = Depends(get_db)) -> list[TokenNetworkResponse]:
    result = crud.get_available_tokens_and_networks(db)
    return result


@app.post(
    "/alerts",
    response_model=schemas.Alert,
    status_code=201,
)
def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)) -> schemas.Alert:
    """Create a new alert.

    Validates the primary market constraint (only available on Ethereum) and delegates
    creation to crud.create_alert. Returns the created alert as AlertRead.
    """
    if alert.is_primary_market and alert.network != "ethereum":
        raise HTTPException(
            status_code=400, detail="Primary market is only available on Ethereum"
        )

    if not crud.check_available_token_network_market_type(
        db, alert.token_name, alert.network, alert.is_primary_market
    ):
        raise HTTPException(
            status_code=400,
            detail="The specified token, network, and market type combination is not available.",
    )

    alert_created: schemas.Alert = crud.create_alert(db, alert)
    return alert_created
