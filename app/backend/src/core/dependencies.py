from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.security import decode_token
from src.db.session import get_db
from src.db.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
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
        print(f"DEBUG: Received token: {token[:20]}...")  # Log parcial do token

        payload = decode_token(token)
        print(f"DEBUG: Decoded payload: {payload}")  # Log do payload

        # Check token type
        if payload.get("type") != "access":
            print(f"DEBUG: Wrong token type: {payload.get('type')}")
            raise credentials_exception

        user_id_str: str | None = payload.get("sub")
        print(f"DEBUG: User ID string from token: {user_id_str}")

        if user_id_str is None:
            print("DEBUG: User ID is None")
            raise credentials_exception

        user_id = int(user_id_str)
        print(f"DEBUG: User ID as int: {user_id}")

    except (ValueError, TypeError) as e:
        print(f"DEBUG: ValueError/TypeError during token decode: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        raise credentials_exception

    # Fetch user from database
    print(f"DEBUG: Fetching user with ID: {user_id}")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        print(f"DEBUG: User not found in database")
        raise credentials_exception

    print(f"DEBUG: User found: {user.email}")
    return user
