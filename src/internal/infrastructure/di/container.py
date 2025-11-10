"""
Dependency Injection Container for Infrastructure.

Provides infrastructure-level dependencies (database sessions, repositories, UoW).
Only contains providers that depend on concrete infrastructure implementations.
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.repositories import UnitOfWork
from internal.infrastructure.persistence.sqlalchemy import (
    async_session_factory,
    SQLAlchemyUnitOfWork,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.
    
    Yields:
        AsyncSession for database operations
    """
    async with async_session_factory() as session:
        yield session


async def get_uow(
    session: AsyncSession = Depends(get_session)
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Get Unit of Work dependency.
    
    Args:
        session: Database session from dependency
        
    Yields:
        UnitOfWork instance for managing transactions
    """
    async with SQLAlchemyUnitOfWork(session) as uow:
        yield uow
