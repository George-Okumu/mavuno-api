from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import decode_token

# HTTPBearer reads the "Authorization: Bearer <token>" header automatically
_bearer = HTTPBearer(auto_error=True)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """
    FastAPI dependency.  Validates the access token and returns the user ID.

    Usage:
        @router.get("/me")
        async def me(user_id: str = Depends(get_current_user_id)):
            ...
    """
    try:
        user_id = decode_token(credentials.credentials, expected_kind="access")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
