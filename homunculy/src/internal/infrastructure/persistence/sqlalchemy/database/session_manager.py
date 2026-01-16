"""Database session management utilities."""

from collections.abc import AsyncGenerator

from settings.database import database_settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""


engine: AsyncEngine = create_async_engine(
    database_settings.uri,
    echo=database_settings.echo,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for DI."""

    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Initialize database tables."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""

    await engine.dispose()
