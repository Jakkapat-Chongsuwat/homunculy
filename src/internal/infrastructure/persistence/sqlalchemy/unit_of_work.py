"""
SQLAlchemy Unit of Work Implementation.

Manages database transactions and provides repository access.
Implements the Unit of Work pattern from Clean Architecture.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.repositories import UnitOfWork
from .agent_repository import SQLAlchemyAgentRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    """
    SQLAlchemy-based Unit of Work.
    
    Manages transactions and provides access to repositories.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize Unit of Work.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.agents = SQLAlchemyAgentRepository(session)
    
    async def __aenter__(self):
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if exc_type is not None:
            await self.rollback()
        await self.session.close()
    
    async def commit(self):
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        await self.session.rollback()
