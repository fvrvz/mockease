from __future__ import annotations

import pytest
from httpx import AsyncClient

from src.models.user import User
from src.services.auth_service import hash_password, create_access_token



@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    payload = {
        "email": "newuser@mockease.dev",
        "username": "newuser",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@mockease.dev"
    assert data["username"] == "newuser"
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User) -> None:
    payload = {
        "email": test_user.email,
        "username": "distinctusername",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, test_user: User) -> None:
    payload = {
        "email": "distinct@mockease.dev",
        "username": test_user.username,
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already taken" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User) -> None:
    payload = {
        "email": test_user.email,
        "password": "securepassword123",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user: User) -> None:
    payload = {
        "email": test_user.email,
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient) -> None:
    payload = {
        "email": "nonexistent@mockease.dev",
        "password": "wrongpassword",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_user: User, auth_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_login_account_disabled(client: AsyncClient, db_session) -> None:  # type: ignore[no-untyped-def]
    disabled_user = User(
        email="disabled@mockease.dev",
        username="disableduser",
        password_hash=hash_password("password123"),
        is_active=False,
    )
    db_session.add(disabled_user)
    await db_session.commit()

    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "disabled@mockease.dev", "password": "password123"},
    )
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_me_invalid_tokens(client: AsyncClient) -> None:
    # Invalid JWT signature/format
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401

    # Token with missing subject claim
    bad_payload_token = create_access_token({})
    res2 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_payload_token}"})
    assert res2.status_code == 401

    # Token with non-existent user ID
    ghost_token = create_access_token({"sub": "00000000-0000-0000-0000-000000000000"})
    res3 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert res3.status_code == 401

