from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class AuthChallengeRequest(BaseModel):
    email: EmailStr


class AuthChallengeResponse(BaseModel):
    expires_at: datetime


class AuthLoginRequest(BaseModel):
    email: EmailStr
    code: str

    @field_validator("code")
    def validate_code(cls, value):
        if not value.isdigit() or len(value) != 6:
            raise ValueError("code must be a 6-digit numeric string")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AuthenticatedUser(BaseModel):
    email: EmailStr
