"""
Database session management.

Provides async SQLAlchemy engine and session factory.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from settings.database import database_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine
engine: AsyncEngine = create_async_engine(
    database_settings.uri,
    echo=database_settings.echo,
    future=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncSession:
    """
    Get database session.
    
    Used for dependency injection in FastAPI.
    """
    async with async_session_factory() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()
