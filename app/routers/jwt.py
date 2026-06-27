from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

#  Config

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

TokenKind = Literal["access", "refresh"]


# Token creation

def _create_token(subject: str, kind: TokenKind, expires_delta: timedelta) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "kind": kind,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        kind="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        kind="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


# Token decoding

def decode_token(token: str, expected_kind: TokenKind = "access") -> str:
    """
    Decode and validate a JWT. Returns the user ID (sub) on success.
    Raises ValueError with a human-readable message on any failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc

    if payload.get("kind") != expected_kind:
        raise ValueError(f"Expected a {expected_kind} token.")

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise ValueError("Token missing subject claim.")

    return user_id
