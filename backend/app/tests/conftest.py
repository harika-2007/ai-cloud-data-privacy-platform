"""Test session configuration and shared fixtures.

Provides fixtures for database sessions, test clients, authentication,
and sample data across all test modules.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.models.user import User
from app.schemas.auth import TokenPayload

# ---------------------------------------------------------------------------
# Use SQLite for fast, isolated test runs
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)
test_async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Database session fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated async database session for testing.

    Rolls back any uncommitted changes after the test completes.
    """
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.rollback()
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def app(db_session: AsyncSession) -> FastAPI:
    """Create a FastAPI application instance with a test database session.

    Overrides the get_db dependency to use the test database.
    """
    # Import here to avoid circular imports at module level
    from server import create_app

    application = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX async test client for the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a standard test user in the database."""
    user = User(
        id="test-user-id",
        name="Test User",
        email="testuser@example.com",
        password_hash=hash_password("TestPass123"),
        role="user",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin test user in the database."""
    user = User(
        id="admin-user-id",
        name="Admin User",
        email="adminuser@example.com",
        password_hash=hash_password("AdminPass123"),
        role="admin",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive (deactivated) test user."""
    user = User(
        id="inactive-user-id",
        name="Inactive User",
        email="inactive@example.com",
        password_hash=hash_password("InactivePass123"),
        role="user",
        is_active=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Auth token fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_token_payload(test_user: User) -> TokenPayload:
    """Create a TokenPayload for the standard test user."""
    return TokenPayload(
        sub=test_user.id,
        role=test_user.role,
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        type="access",
        iat=int(datetime.now(timezone.utc).timestamp()),
    )


@pytest.fixture
def admin_token_payload(admin_user: User) -> TokenPayload:
    """Create a TokenPayload for the admin test user."""
    return TokenPayload(
        sub=admin_user.id,
        role=admin_user.role,
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        type="access",
        iat=int(datetime.now(timezone.utc).timestamp()),
    )


@pytest.fixture
def user_auth_headers(test_user: User) -> dict[str, str]:
    """Generate Authorization headers with a valid access token for the test user."""
    token = create_access_token(subject=test_user.id, role=test_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """Generate Authorization headers with a valid access token for the admin user."""
    token = create_access_token(subject=admin_user.id, role=admin_user.role)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Mock fixtures for unit tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db_session():
    """Create a mock async database session for service-level tests."""
    return AsyncMock()


@pytest.fixture
def mock_user_repo(mock_db_session):
    """Create a mock UserRepository for service-level tests."""
    from app.repositories.user_repository import UserRepository

    return UserRepository(mock_db_session)
