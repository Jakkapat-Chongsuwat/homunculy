"""SQLAlchemy Unit of Work implementation."""

from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.repositories import UnitOfWork

from .agent_repository import SQLAlchemyAgentRepository


class SQLAlchemyUnitOfWork(UnitOfWork):
    """Unit of Work backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.agents = SQLAlchemyAgentRepository(session)

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
