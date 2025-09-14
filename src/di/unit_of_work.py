import abc
from abc import abstractmethod
from typing import Any, Generic, Optional, Type, TypeVar

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.abstraction import AbstractPokemonRepository
from repositories.abstraction.ai_agent import AbstractAIAgentRepository
from repositories.document_db import MongoDBPokemonRepository
from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository
from repositories.key_value_db import RedisPokemonRepository
from repositories.key_value_db.ai_agent.repository import RedisAIAgentRepository
from repositories.relational_db import RelationalDBPokemonRepository
from repositories.relational_db.ai_agent.repository import RelationalDBAIAgentRepository

# pylint: disable=import-outside-toplevel,attribute-defined-outside-init


T = TypeVar('T', bound=AbstractPokemonRepository)
U = TypeVar('U', bound=AbstractAIAgentRepository)


# Domain-specific Unit of Work base classes
class AbstractPokemonUnitOfWork(abc.ABC):
    pokemon_repo: AbstractPokemonRepository

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError


class AbstractAIAgentUnitOfWork(abc.ABC):
    ai_agent_repo: AbstractAIAgentRepository

    @abstractmethod
    async def __aenter__(self):
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError


# Legacy mixed-domain UoW (for backward compatibility during migration)
class AbstractUnitOfWork(Generic[T], abc.ABC):
    pokemon_repo: AbstractPokemonRepository
    ai_agent_repo: AbstractAIAgentRepository

    def __init__(self, pokemon_repo: T):
        self.pokemon_repo = pokemon_repo

    @abstractmethod
    async def __aenter__(self) -> 'AbstractUnitOfWork[T]':
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        raise NotImplementedError


# Concrete implementations for Pokemon domain
class RelationalPokemonUnitOfWork(AbstractPokemonUnitOfWork):
    def __init__(self, session: AsyncSession, pokemon_repo: RelationalDBPokemonRepository):
        self._session = session
        self.pokemon_repo = pokemon_repo

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
        # Note: In async context, this would be called within the context manager
        # The actual commit happens in __aexit__ if no exception
        pass

    def rollback(self):
        # Note: In async context, this would be called within the context manager
        # The actual rollback happens in __aexit__ if there's an exception
        pass


class MongoDBPokemonUnitOfWork(AbstractPokemonUnitOfWork):
    def __init__(self, engine: AsyncIOMotorClient, pokemon_repo: MongoDBPokemonRepository):
        self._engine = engine
        self.pokemon_repo = pokemon_repo

    async def __aenter__(self):
        self._session = await self._engine.start_session()
        self._session.start_transaction()
        self.pokemon_repo.session = self._session
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any):
        try:
            if exc_type is None:
                await self._session.commit_transaction()
            else:
                await self._session.abort_transaction()
        finally:
            await self._session.end_session()

    def commit(self):
        # For MongoDB, commit is handled in __aexit__
        # This method is here for interface compliance
        pass

    def rollback(self):
        # For MongoDB, rollback is handled in __aexit__
        # This method is here for interface compliance
        pass


class RedisPokemonUnitOfWork(AbstractPokemonUnitOfWork):
    def __init__(self, client: AsyncRedis, pokemon_repo: RedisPokemonRepository):
        self._client = client
        self.pokemon_repo = pokemon_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any):
        await self._client.aclose()  # type: ignore

    def commit(self):
        # Redis doesn't support transactions in the same way as relational databases
        # This method is here for interface compliance
        pass

    def rollback(self):
        # Redis doesn't support transactions in the same way as relational databases
        # This method is here for interface compliance
        pass


# Concrete implementations for AI Agent domain
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
        # Note: In async context, this would be called within the context manager
        # The actual commit happens in __aexit__ if no exception
        pass

    def rollback(self):
        # Note: In async context, this would be called within the context manager
        # The actual rollback happens in __aexit__ if there's an exception
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
        # For MongoDB, commit is handled in __aexit__
        # This method is here for interface compliance
        pass

    def rollback(self):
        # For MongoDB, rollback is handled in __aexit__
        # This method is here for interface compliance
        pass


class RedisAIAgentUnitOfWork(AbstractAIAgentUnitOfWork):
    def __init__(self, client: AsyncRedis, ai_agent_repo: AbstractAIAgentRepository):
        self._client = client
        self.ai_agent_repo = ai_agent_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any):
        await self._client.aclose()  # type: ignore

    def commit(self):
        # Redis doesn't support transactions in the same way as relational databases
        # This method is here for interface compliance
        pass

    def rollback(self):
        # Redis doesn't support transactions in the same way as relational databases
        # This method is here for interface compliance
        pass


class AsyncSQLAlchemyUnitOfWork(AbstractUnitOfWork[RelationalDBPokemonRepository]):
    def __init__(self, session: AsyncSession, pokemon_repo: RelationalDBPokemonRepository, ai_agent_repo: AbstractAIAgentRepository):
        super().__init__(pokemon_repo)
        self._session = session
        # Initialize AI agent repository
        self.ai_agent_repo = ai_agent_repo

    async def __aenter__(self):
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any
    ):
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

        # https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.async_scoped_session.remove
        await AsyncScopedSession.remove()


class AsyncMotorUnitOfWork(AbstractUnitOfWork[MongoDBPokemonRepository]):
    def __init__(
        self,
        engine: AsyncIOMotorClient,  # pyright: ignore[reportInvalidTypeForm]
        pokemon_repo: MongoDBPokemonRepository,
        ai_agent_repo: AbstractAIAgentRepository,
    ):
        super().__init__(pokemon_repo)
        self._engine = engine
        # Initialize AI agent repository
        self.ai_agent_repo = ai_agent_repo

    async def __aenter__(self):
        self._session = await self._engine.start_session()
        self._session.start_transaction()
        self.pokemon_repo.session = self._session

        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any
    ):
        try:
            if exc_type is None:
                await self._session.commit_transaction()
            else:
                await self._session.abort_transaction()
        finally:
            await self._session.end_session()


class AsyncRedisUnitOfWork(AbstractUnitOfWork[RedisPokemonRepository]):
    """
    This implementation does not support transactions.

    If transaction-like behavior is required, compensating actions must be implemented manually.

    Compensating actions are a series of operations that revert the effects of the preceding operations
    in case of failure, ensuring data consistency.

    For more information, see: https://en.wikipedia.org/wiki/Compensating_transaction
    """

    def __init__(self, client: AsyncRedis, pokemon_repo: RedisPokemonRepository, ai_agent_repo: AbstractAIAgentRepository):
        self._client = client
        super().__init__(pokemon_repo)
        # Initialize AI agent repository
        self.ai_agent_repo = ai_agent_repo

    async def __aenter__(self):
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc: Optional[BaseException], tb: Any
    ) -> None:
        # Not supported yet, see https://github.com/python/typeshed/blob/main/stubs/redis/redis/asyncio/client.pyi#L27
        await self._client.aclose()  # type: ignore
