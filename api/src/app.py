import logging
import threading
from contextlib import asynccontextmanager, suppress
from time import monotonic

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

import models
from database import SessionLocal, engine
from rate_limiting import limiter
from routers import alerts as alerts_router
from routers import auth as auth_router
from routers import prices as prices_router
from services import alerting

ALERT_CHECK_INTERVAL_SECONDS = 600
logger = logging.getLogger(__name__)


def _alert_check_worker(stop_event: threading.Event) -> None:
    logger.info("Alert check worker started")
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


def create_app() -> FastAPI:
    models.Base.metadata.create_all(bind=engine)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app = FastAPI(
        title="ETH LST tracker API",
        summary="API to track prices and premiums of various Ethereum Liquid Staking Tokens (LST).",
        docs_url=None,
        redoc_url="/docs",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.include_router(auth_router.router)
    app.include_router(alerts_router.router)
    app.include_router(prices_router.router)
    return app
