import abc
from abc import abstractmethod
from typing import Any, Generic, Optional, Type, TypeVar

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.abstraction.ai_agent import AbstractAIAgentRepository
from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository
from repositories.relational_db.ai_agent.repository import RelationalDBAIAgentRepository

# pylint: disable=import-outside-toplevel,attribute-defined-outside-init



"""
Unit of Work implementations and best-practice guidance.

This module exposes Unit of Work interfaces and concrete implementations
for the AI Agent domain. It intentionally focuses on per-transaction UoW
instances that are created and disposed inside use-cases (application
layer). The file also documents concise best-practices for working with
UoWs in an async application.

Best practices (short):
- Create a fresh UoW per logical transaction (HTTP request, WebSocket message).
- Use UoW as an async context manager: `async with uow: ...` so commit/rollback
  and cleanup run automatically in `__aexit__`.
- Keep UoW small: it should only expose repository interfaces bound to the
  same underlying session/connection and lifecycle methods (commit/rollback).
- UoW implementations must always close and remove scoped sessions in
  `__aexit__` to avoid session leakage across asyncio tasks.
- Providers (DI) should return UoW instances (or factories) but must not
  execute business logic.

The code below contains concrete UoW classes for relational, MongoDB and
Redis-backed AI agent repositories.
"""

from typing import Any, Optional, Type

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.abstraction.ai_agent import AbstractAIAgentRepository


class AbstractAIAgentUnitOfWork:
    """Abstract UoW interface for AI agent domain.

    Implementations must provide `ai_agent_repo` and async context manager
    semantics for transactional behavior.
    """

    ai_agent_repo: AbstractAIAgentRepository

    async def __aenter__(self):
        raise NotImplementedError

    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError

    def commit(self):
        raise NotImplementedError

    def rollback(self):
        raise NotImplementedError


class RelationalAIAgentUnitOfWork(AbstractAIAgentUnitOfWork):
    def __init__(self, session: AsyncSession, ai_agent_repo: AbstractAIAgentRepository):
        self._session = session
        self.ai_agent_repo = ai_agent_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any):
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()
            await self.remove()

    async def remove(self):
        from settings.db import AsyncScopedSession

        await AsyncScopedSession.remove()

    def commit(self):
        pass

    def rollback(self):
        pass


class MongoDBAIAgentUnitOfWork(AbstractAIAgentUnitOfWork):
    def __init__(self, engine: AsyncIOMotorClient, ai_agent_repo: AbstractAIAgentRepository):
        self._engine = engine
        self.ai_agent_repo = ai_agent_repo
        self._session: Optional[Any] = None

    async def __aenter__(self):
        self._session = await self._engine.start_session()
        self._session.start_transaction()
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any):
        if self._session is None:
            return
        try:
            if exc_type is None:
                await self._session.commit_transaction()
            else:
                await self._session.abort_transaction()
        finally:
            await self._session.end_session()

    def commit(self):
        pass

    def rollback(self):
        pass


class AsyncSQLAlchemyUnitOfWork(RelationalAIAgentUnitOfWork):
    def __init__(self, session: AsyncSession, ai_agent_repo: AbstractAIAgentRepository):
        super().__init__(session, ai_agent_repo)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any):
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()
            await self.remove()
