"""Test authentication endpoints."""

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test user registration."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "hashed_password" not in data
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User) -> None:
    """Test registration with duplicate email fails."""
    response = await client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "password": "password123",
            "full_name": "Duplicate User",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User) -> None:
    """Test successful login."""
    response = await client.post(
        "/auth/login",
        auth=("test@example.com", "testpassword123"),
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User) -> None:
    """Test login with wrong password fails."""
    response = await client.post(
        "/auth/login",
        auth=("test@example.com", "wrongpassword"),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Test login with nonexistent user fails."""
    response = await client.post(
        "/auth/login",
        auth=("nonexistent@example.com", "password123"),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(
    client: AsyncClient, test_user: User, auth_headers: dict[str, str]
) -> None:
    """Test getting current user with valid token."""
    response = await client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient) -> None:
    """Test getting current user without token fails."""
    response = await client.get("/auth/me")

    assert response.status_code == 403  # HTTPBearer returns 403 when no credentials


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient) -> None:
    """Test getting current user with invalid token fails."""
    response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user: User) -> None:
    """Test refresh token generates new access and refresh tokens.

    This test validates the complete refresh flow:
    1. Login to get initial tokens
    2. Use refresh token to get new tokens
    3. Verify new tokens are different from original
    4. Verify new access token works for authenticated requests
    """
    # Step 1: Login to get initial tokens
    login_response = await client.post(
        "/auth/login",
        auth=("test@example.com", "testpassword123"),
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Wait 1 second to ensure new tokens have different exp timestamp
    await asyncio.sleep(1)

    # Step 2: Use refresh token to get new tokens
    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    # This should pass but currently FAILS with 401 due to UUID bug
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"

    # Step 3: Verify new tokens are different (rotated)
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Step 4: Verify new access token works for authenticated requests
    me_response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
    )
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == test_user.email


@pytest.mark.asyncio
async def test_refresh_token_with_invalid_format(client: AsyncClient) -> None:
    """Test refresh token endpoint rejects malformed tokens."""
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": "not-a-valid-jwt-token"},
    )

    assert response.status_code == 401
    assert "Could not validate" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_with_access_token(client: AsyncClient, test_user: User) -> None:
    """Test refresh token endpoint rejects access tokens (wrong type)."""
    # Login to get tokens
    login_response = await client.post(
        "/auth/login",
        auth=("test@example.com", "testpassword123"),
    )
    tokens = login_response.json()

    # Try to refresh using access token instead of refresh token
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["access_token"]},  # Wrong token type!
    )

    assert response.status_code == 401
    assert "Could not validate" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_with_expired_token(client: AsyncClient) -> None:
    """Test refresh token endpoint rejects expired tokens.

    Note: This creates a token with exp in the past to simulate expiration.
    """
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from src.core.config import get_settings

    settings = get_settings()

    # Create an expired refresh token (exp 1 hour ago)
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "type": "refresh",
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": expired_token},
    )

    assert response.status_code == 401
    assert "Could not validate" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_with_nonexistent_user(client: AsyncClient) -> None:
    """Test refresh token endpoint rejects tokens for users that don't exist."""
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from src.core.config import get_settings

    settings = get_settings()

    # Create a valid token for a non-existent user
    fake_user_payload = {
        "sub": "00000000-0000-0000-0000-000000000000",  # Non-existent UUID
        "exp": datetime.now(UTC) + timedelta(days=7),
        "type": "refresh",
    }
    fake_token = jwt.encode(
        fake_user_payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": fake_token},
    )

    assert response.status_code == 401
    assert "Could not validate" in response.json()["detail"]
