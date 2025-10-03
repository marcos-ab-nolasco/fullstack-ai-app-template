from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.db.models.user import User
from src.db.session import get_db


@lru_cache
def _get_http_bearer() -> HTTPBearer:
    """Return cached HTTP bearer scheme."""

    return HTTPBearer()


async def get_http_bearer_credentials(
    request: Request,
) -> HTTPAuthorizationCredentials:
    """Resolve bearer credentials using cached scheme."""

    return await _get_http_bearer()(request)  # type: ignore[return-value]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_http_bearer_credentials)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception

        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        user_id = int(user_id_str)

    except (ValueError, TypeError) as e:
        raise credentials_exception from e

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
