from datetime import datetime

from pydantic import BaseModel, EmailStr


class AuthChallengeRequest(BaseModel):
    email: EmailStr


class AuthChallengeResponse(BaseModel):
    expires_at: datetime


class AuthLoginRequest(BaseModel):
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthenticatedUser(BaseModel):
    email: EmailStr
