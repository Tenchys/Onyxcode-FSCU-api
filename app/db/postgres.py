"""Postgres connection client with small pool and strict timeouts."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine as sa_create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import get_settings


def _build_sync_url(settings_module=None) -> str:
    """Build sync database URL from components or use existing DATABASE_URL."""
    s = get_settings()
    if s.database_url:
        return s.database_url
    return (
        f"postgresql://{s.postgres_user}:{s.postgres_password}"
        f"@{s.postgres_host}:{s.postgres_port}/{s.postgres_db}"
    )


def _build_async_url() -> str:
    """Build async database URL for SQLAlchemy asyncio support."""
    s = get_settings()
    if s.database_url:
        # Convert postgresql:// to postgresql+asyncpg:// if needed
        url = s.database_url
        if url.startswith("postgresql://") and "+" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    return (
        f"postgresql+asyncpg://{s.postgres_user}:{s.postgres_password}"
        f"@{s.postgres_host}:{s.postgres_port}/{s.postgres_db}"
    )


def create_sync_engine():
    """Create sync engine with small pool and statement timeout."""
    settings = get_settings()
    url = _build_sync_url()
    engine = create_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_max_overflow,
        pool_pre_ping=True,
        # Statement timeout applied at session level, not engine
    )
    return engine


def create_async_engine():
    """Create async engine with small pool."""
    settings = get_settings()
    url = _build_async_url()
    engine = sa_create_async_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_max_overflow,
        pool_pre_ping=True,
        poolclass=NullPool if settings.app_env == "testing" else None,
    )
    return engine


# Module-level engine instances (lazy, created once)
_sync_engine = None
_async_engine = None


def get_sync_engine():
    """Return the sync engine singleton."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_sync_engine()
    return _sync_engine


def get_async_engine():
    """Return the async engine singleton."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine()
    return _async_engine


def get_async_session_factory():
    """Return an async session factory bound to the async engine."""
    return async_sessionmaker(
        bind=get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a single async DB session with statement timeout active."""
    settings = get_settings()
    factory = get_async_session_factory()
    async with factory() as session:
        # Set statement_timeout for this session
        await session.execute(
            text(f"SET statement_timeout = {settings.db_statement_timeout_ms}")
        )
        try:
            yield session
        finally:
            await session.close()
