from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.main import app
from src.db.base import Base
from src.db.session import get_db
from src.models.user import User
from src.services.auth_service import hash_password, create_access_token
import src.models  # noqa: F401
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

# Teach SQLite compiler how to render PostgreSQL-specific JSONB and UUID types in tests
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):  # type: ignore[no-untyped-def]
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):  # type: ignore[no-untyped-def]
    return "CHAR(36)"

# In-memory SQLite async engine for tests
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def mock_redis_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cache_store: dict[str, Any] = {}

    async def fake_cache_get(key: str) -> Any | None:
        return cache_store.get(key)

    async def fake_cache_set(key: str, value: Any, ttl: int = 300) -> None:
        cache_store[key] = value

    async def fake_cache_delete(key: str) -> None:
        cache_store.pop(key, None)

    async def fake_cache_delete_pattern(pattern: str) -> None:
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in cache_store if prefix in k]
        for k in keys_to_del:
            cache_store.pop(k, None)

    monkeypatch.setattr("src.cache.redis.cache_get", fake_cache_get)
    monkeypatch.setattr("src.cache.redis.cache_set", fake_cache_set)
    monkeypatch.setattr("src.cache.redis.cache_delete", fake_cache_delete)
    monkeypatch.setattr("src.cache.redis.cache_delete_pattern", fake_cache_delete_pattern)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="test@mockease.dev",
        username="testuser",
        password_hash=hash_password("securepassword123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
