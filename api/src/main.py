import logging
import os
import threading
from contextlib import suppress, asynccontextmanager
from time import monotonic

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import alerting
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
ALERT_CHECK_INTERVAL_SECONDS = 600

EMAIL_RECIPIENT_WHITELIST = os.getenv("EMAIL_RECIPIENT_WHITELIST", "").split(",")


def _alert_check_worker(stop_event: threading.Event) -> None:
    logger.info(f"Alert check worker started")
    next_run = monotonic()
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                alerting.run_alert_checks(db)
            finally:
                db.close()
        except Exception:  # pragma: no cover - defensive logging
            logger.exception("Failed to execute alert checks")

        next_run += ALERT_CHECK_INTERVAL_SECONDS
        delay = max(0, next_run - monotonic())
        if stop_event.wait(delay):
            break

@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_alert_check_worker,
        args=(stop_event,),
        name="alert-check-worker",
        daemon=True,
    )
    thread.start()
    app.state.alert_check_stop_event = stop_event
    app.state.alert_check_thread = thread

    yield

    stop_event = getattr(app.state, "alert_check_stop_event", None)
    thread = getattr(app.state, "alert_check_thread", None)
    if stop_event is not None:
        stop_event.set()
    if thread is not None:
        with suppress(RuntimeError):
            thread.join()


app = FastAPI(
    title="ETH LST tracker API",
    summary="API to track prices and premiums of various Ethereum Liquid Staking Tokens (LST).",
    docs_url=None,
    redoc_url="/docs",
    lifespan=lifespan,
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
    if len(EMAIL_RECIPIENT_WHITELIST) > 0 and alert.email not in EMAIL_RECIPIENT_WHITELIST:
        raise HTTPException(
            status_code=400,
            detail="Email recipient is not in the allowed whitelist.",
        )

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
