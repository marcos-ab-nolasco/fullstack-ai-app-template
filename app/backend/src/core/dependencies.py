import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.db.models.user import User
from src.db.session import get_db

http_bearer_scheme = HTTPBearer()

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = decode_token(token)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid token: reason=decode_failed error={str(e)}")
        raise credentials_exception from e

    # Check token type
    if payload.get("type") != "access":
        logger.warning(f"Invalid token: reason=wrong_token_type token_type={payload.get('type')}")
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        logger.warning("Invalid token: reason=missing_subject")
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid token: reason=invalid_uuid_format user_id_str={user_id_str}")
        raise credentials_exception from e

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"Invalid token: reason=user_not_found user_id={user_id}")
        raise credentials_exception

    # Store user_id in request state for middleware logging
    request.state.user_id = str(user_id)

    return user
