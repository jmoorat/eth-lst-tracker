"""Passwordless email authentication helpers."""

import hashlib
import os
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

import models
from schemas.auth import AuthenticatedUser
from utils.email import send_mail_notification

CHALLENGE_TTL_SECONDS = int(os.getenv("AUTH_CHALLENGE_TTL_SECONDS", "900"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_EXPIRATION_SECONDS = int(os.getenv("JWT_EXPIRATION_SECONDS", "3600"))
MAGIC_LINK_BASE_URL = os.getenv("AUTH_MAGIC_LINK_BASE_URL", "")
JWT_ALGORITHM = "HS256"


class AuthError(Exception):
    """Base class for authentication errors."""


class InvalidAuthChallengeError(AuthError):
    """Raised when a login challenge cannot be validated."""


class TokenExpiredError(AuthError):
    """Raised when a token is expired."""


class InvalidTokenError(AuthError):
    """Raised when a token cannot be decoded or validated."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def create_auth_challenge(db: Session, email: str) -> tuple[models.AuthChallenge, str]:
    """Create and persist a passwordless challenge for the email."""

    challenge = models.AuthChallenge(
        email=email,
        code_hash=_hash_code(code := _generate_code()),
        expires_at=_now() + timedelta(seconds=CHALLENGE_TTL_SECONDS),
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge, code


def send_challenge_email(email: str, code: str) -> None:
    """Deliver the challenge code via email."""

    link = ""
    if MAGIC_LINK_BASE_URL:
        query = urllib.parse.urlencode({"email": email, "code": code})
        link = f"\n\nMagic link: {MAGIC_LINK_BASE_URL}?{query}"

    subject = "Your ETH LST Tracker login code"
    body = (
        "Use the following one-time code to finish logging in to the ETH LST Tracker API:"
        f"\n\n{code}\n\nThis code expires in {CHALLENGE_TTL_SECONDS // 60} minutes.{link}\n\n"
        "If you did not request this code you can safely ignore this email."
    )
    send_mail_notification(email, subject, body)


def validate_auth_challenge(db: Session, email: str, code: str) -> models.AuthChallenge:
    """Validate and consume the most recent challenge for the user."""

    challenge = (
        db.query(models.AuthChallenge)
        .filter(
            models.AuthChallenge.email == email,
            models.AuthChallenge.expires_at > _now(),
            models.AuthChallenge.consumed_at.is_(None),
        )
        .order_by(models.AuthChallenge.created_at.desc())
        .first()
    )

    if challenge is None or challenge.code_hash != _hash_code(code):
        raise InvalidAuthChallengeError("Invalid or expired login code.")

    challenge.consumed_at = _now()
    db.commit()
    db.refresh(challenge)
    return challenge


def _require_jwt_secret() -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY must be configured for email authentication to work.")
    return JWT_SECRET_KEY


def create_access_token(email: str) -> tuple[str, datetime]:
    """Create a signed JWT for the provided email."""

    secret = _require_jwt_secret()
    now = _now()
    expires_at = now + timedelta(seconds=JWT_EXPIRATION_SECONDS)
    payload = {"sub": email, "iat": int(now.timestamp()), "exp": int(expires_at.timestamp())}
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_access_token(token: str) -> AuthenticatedUser:
    """Decode and verify a JWT returning the authenticated user."""

    secret = _require_jwt_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:  # pragma: no cover - defensive programming
        raise InvalidTokenError("Invalid token.") from exc

    email = payload.get("sub")
    if not email:
        raise InvalidTokenError("Token payload is missing subject.")

    return AuthenticatedUser(email=email)
