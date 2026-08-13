"""
Database engine and session management.
Supports PostgreSQL (production) and SQLite (development fallback).
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from typing import AsyncGenerator

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


from sqlalchemy.pool import StaticPool

def _get_engine_kwargs() -> dict:
    """Get engine configuration based on database type."""
    url = settings.DATABASE_URL
    kwargs: dict = {
        "echo": settings.DATABASE_ECHO,
    }
    if "sqlite" in url:
        # StaticPool ensures only ONE connection is used across all threads
        # This completely prevents SQLite "database is locked" deadlocks in FastAPI
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 3600
    return kwargs


engine = create_async_engine(settings.DATABASE_URL, **_get_engine_kwargs())

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables. Called on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine. Called on application shutdown."""
    await engine.dispose()
