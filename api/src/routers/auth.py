import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from rate_limiting import limiter
from schemas.auth import (
    AuthChallengeRequest,
    AuthChallengeResponse,
    AuthLoginRequest,
    TokenResponse,
)
from services import auth

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
AUTH_RATE_LIMIT = "5/minute"


@router.post(
    "/challenge",
    response_model=AuthChallengeResponse,
    status_code=202,
)
@limiter.limit(AUTH_RATE_LIMIT)
def request_auth_challenge(
    request: Request,  # required for SlowAPI rate limiting
    payload: AuthChallengeRequest,
    db: Session = Depends(get_db),
) -> AuthChallengeResponse:
    challenge, code = auth.create_auth_challenge(db, payload.email)
    try:
        auth.send_challenge_email(payload.email, code)
    except Exception as exc:  # pragma: no cover - depends on SMTP availability
        logger.exception("Failed to send login code to %s", payload.email)
        raise HTTPException(status_code=500, detail="Unable to send login code.") from exc
    return AuthChallengeResponse(expires_at=challenge.expires_at)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
def finalize_login(
    request: Request,  # required for SlowAPI rate limiting
    payload: AuthLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        auth.validate_auth_challenge(db, payload.email, payload.code)
    except auth.InvalidAuthChallengeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    token, expires_at = auth.create_access_token(payload.email)
    return TokenResponse(access_token=token, expires_at=expires_at)
