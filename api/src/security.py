from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.auth import AuthenticatedUser
from services import auth

auth_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authentication token.")
    try:
        return auth.decode_access_token(credentials.credentials)
    except auth.TokenExpiredError as exc:
        raise HTTPException(status_code=401, detail="Token has expired.") from exc
    except auth.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
