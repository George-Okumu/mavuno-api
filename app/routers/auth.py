from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext

from app.db.neo4j import get_session
from .dependencies import get_current_user_id
from .jwt import create_access_token, create_refresh_token, decode_token
from ..models.schemas import AuthOut, LoginIn, MessageOut, RefreshIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash(plain: str) -> str:
    return _pwd.hash(plain)


def _verify(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# Shared helpers

def _build_auth_response(user: UserOut) -> AuthOut:
    return AuthOut(
        accessToken=create_access_token(user.userId),
        refreshToken=create_refresh_token(user.userId),
        user=user,
    )


def _row_to_user(record: dict) -> UserOut:
    """Map a raw Neo4j record dict (node properties) to UserOut."""
    return UserOut(
        userId=record["userId"],
        name=record["name"],
        email=record["email"],
        role=record["role"],
        phone=record.get("phone"),
        region=record.get("region"),
        createdAt=record.get("createdAt"),
    )


# Cypher queries

_FIND_BY_EMAIL = """
MATCH (u:User {email: $email})
RETURN
    u.userId      AS userId,
    u.name        AS name,
    u.email       AS email,
    u.role        AS role,
    u.phone       AS phone,
    u.region      AS region,
    u.hashedPassword AS hashedPassword,
    u.createdAt   AS createdAt
"""

_FIND_BY_ID = """
MATCH (u:User {userId: $userId})
RETURN
    u.userId    AS userId,
    u.name      AS name,
    u.email     AS email,
    u.role      AS role,
    u.phone     AS phone,
    u.region    AS region,
    u.createdAt AS createdAt
"""

_CREATE_USER = """
CREATE (u:User {
    userId:          $userId,
    name:            $name,
    email:           $email,
    role:            $role,
    phone:           $phone,
    region:          $region,
    hashedPassword:  $hashedPassword,
    createdAt:       $createdAt
})
RETURN
    u.userId    AS userId,
    u.name      AS name,
    u.email     AS email,
    u.role      AS role,
    u.phone     AS phone,
    u.region    AS region,
    u.createdAt AS createdAt
"""


# Routes


@router.post(
    "/register",
    response_model=AuthOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new farmer or lender account",
)
async def register(body: RegisterIn):
    """
    Creates a :User node in Neo4j and returns a token pair + user object.

    Node label : User
    Unique key : email
    """
    async with get_session() as session:
        # 1. Guard against duplicate e-mails
        result = await session.run(_FIND_BY_EMAIL, email=body.email)
        existing = await result.single()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

        # 2. Persist the new user
        now = datetime.now(tz=timezone.utc).isoformat()
        result = await session.run(
            _CREATE_USER,
            userId=str(uuid.uuid4()),
            name=body.name,
            email=body.email,
            role=body.role,
            phone=body.phone or "",
            region=body.region or "",
            hashedPassword=_hash(body.password),
            createdAt=now,
        )
        record = await result.single()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user.",
            )

    return _build_auth_response(_row_to_user(dict(record)))


@router.post(
    "/login",
    response_model=AuthOut,
    summary="Authenticate with email and password",
)
async def login(body: LoginIn):
    """
    Looks up the :User node by email, verifies the bcrypt password,
    and returns a token pair + user object.
    """
    async with get_session() as session:
        result = await session.run(_FIND_BY_EMAIL, email=body.email)
        record = await result.single()

    # Deliberate: same error for "not found" and "wrong password"
    # to avoid user-enumeration.
    if not record or not _verify(body.password, record["hashedPassword"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _build_auth_response(_row_to_user(dict(record)))


@router.post(
    "/refresh",
    response_model=AuthOut,
    summary="Exchange a refresh token for a new token pair",
)
async def refresh(body: RefreshIn):
    """
    Validates the refresh token, fetches the :User node by ID,
    and issues a rotated token pair.
    """
    try:
        user_id = decode_token(body.refreshToken, expected_kind="refresh")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    async with get_session() as session:
        result = await session.run(_FIND_BY_ID, userId=user_id)
        record = await result.single()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found — token may be stale.",
        )

    return _build_auth_response(_row_to_user(dict(record)))


@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the currently authenticated user",
)
async def me(user_id: str = Depends(get_current_user_id)):
    """
    Protected route — requires a valid Bearer access token.
    Fetches and returns the :User node matching the token subject.
    """
    async with get_session() as session:
        result = await session.run(_FIND_BY_ID, userId=user_id)
        record = await result.single()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return _row_to_user(dict(record))


@router.post(
    "/logout",
    response_model=MessageOut,
    summary="Invalidate the current session",
)
async def logout(user_id: str = Depends(get_current_user_id)):
    """
    Stateless JWT logout — the client discards its tokens.

    To add server-side revocation (e.g. Redis denylist):
        await redis.setex(f"revoked:{token_jti}", ttl_seconds, "1")
    and check the denylist inside get_current_user_id().
    """
    _ = user_id
    return MessageOut(message="Logged out successfully.")
