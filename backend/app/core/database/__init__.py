"""Database engine and session configuration.

Provides async SQLAlchemy engine, session factory, and dependency injection
for database connections using FastAPI's dependency injection system.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config.settings import settings

# Only pass pool arguments for PostgreSQL (not for SQLite used in tests)
_engine_kwargs = {"echo": settings.DB_ECHO, "pool_pre_ping": True}
if "postgres" in str(settings.DATABASE_URL):
    _engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    _engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_async_engine(
    str(settings.DATABASE_URL),
    **_engine_kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def initialize_database() -> None:
    """Create all tables. Used during application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_database_connection() -> None:
    """Dispose of the engine. Used during application shutdown."""
    await engine.dispose()
