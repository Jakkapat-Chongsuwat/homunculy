"""
Dependency Injection Configuration for the Application.

This module sets up dependency injection for database interactions within the
application. It accommodates both relational and NoSQL databases, providing the
flexibility needed for various database integrations based on application
requirements.

The Injector is tailored with specific modules depending on the database type
specified by environment variables. Each module offers essential components such
as sessions, repositories, and units of work necessary for database operations.

Usage:
    # To obtain a unit of work for database operations, use the following:
    async_unit_of_work = injector.get(AbstractUnitOfWork)

For detailed guidance and advanced use cases of dependency injection in Python,
refer to:
    - https://github.com/python-injector/injector
    - https://github.com/ets-labs/python-dependency-injector
    - https://github.com/ivankorobkov/python-inject
"""

# pylint: disable=import-outside-toplevel


from injector import Injector, Module, provider, singleton
from motor.motor_asyncio import AsyncIOMotorCollection
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.document_db import MongoDBPokemonRepository
from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository
from repositories.key_value_db import RedisPokemonRepository
from repositories.key_value_db.ai_agent.repository import RedisAIAgentRepository
from repositories.relational_db import RelationalDBPokemonRepository
from repositories.relational_db.ai_agent.repository import RelationalDBAIAgentRepository
from repositories.abstraction.ai_agent import AbstractAIAgentRepository
from repositories.llm_service.llm_factory import LLMFactory
from settings.db import IS_DOCUMENT_DB, IS_KEY_VALUE_DB, IS_RELATIONAL_DB

from .unit_of_work import (
    AbstractUnitOfWork,
    AsyncMotorUnitOfWork,
    AsyncRedisUnitOfWork,
    AsyncSQLAlchemyUnitOfWork,
    # New domain-specific UoW classes
    AbstractPokemonUnitOfWork,
    AbstractAIAgentUnitOfWork,
    RelationalPokemonUnitOfWork,
    RelationalAIAgentUnitOfWork,
    MongoDBPokemonUnitOfWork,
    MongoDBAIAgentUnitOfWork,
    RedisPokemonUnitOfWork,
    RedisAIAgentUnitOfWork,
)


class LLMModule(Module):
    """Module for LLM service dependencies."""

    @singleton
    @provider
    def provide_llm_factory(self) -> LLMFactory:
        """Provides the LLM factory for creating LLM clients."""
        return LLMFactory()


class RelationalDBModule(Module):
    @provider
    def provide_async_session(self) -> AsyncSession:
        """Provides an instance of AsyncSession for database operations within an asynchronous context.

        This function is designed to return a scoped session that is unique to the current asyncio task,
        utilizing `asyncio.current_task` as its scope function. This ensures that within a single asyncio task,
        repeated calls to this provider will yield the same AsyncSession instance, promoting session reuse
        and consistency across database operations initiated within the same task context.

        However, it's observed that `provide_async_session` can be invoked multiple times, leading to
        the creation of multiple session instances. This behavior is mitigated by the underlying mechanism
        that binds session instances to the current asyncio task, thus ensuring that within the asyncio
        context, these invocations will still resolve to the same AsyncSession instance.

        Should concerns arise regarding this behavior or if an alternative dependency injection pattern
        is preferred, consider adjusting the session management strategy or exploring other DI tools
        that might offer more granular control over session lifecycle and task scoping.

        Note: The effectiveness of this pattern relies on the proper functioning of `asyncio.current_task`
        for identifying and segregating sessions per task. Misuse or misconfiguration could lead to
        unintended session sharing or leakage across tasks. Ensure thorough testing and understanding
        of the async context and task management in your application.

        Invocation example illustrating the dependency resolution flow when obtaining an AbstractUnitOfWork:

        ```
        injector.get(AbstractUnitOfWork)
            ├─> provide_async_sqlalchemy_unit_of_work()
            │     ├─> provide_async_session()         # Returns a session scoped to the current asyncio task
            │     └─> provide_pokemon_repository()
            │           └─> provide_async_session()   # Reuses the same session instance as above
        ```
        """
        from settings.db import get_async_session

        return get_async_session()

    @provider
    def provide_pokemon_repository(self, session: AsyncSession) -> RelationalDBPokemonRepository:
        return RelationalDBPokemonRepository(session)

    @provider
    def provide_ai_agent_repository(self, session: AsyncSession, llm_factory: LLMFactory) -> AbstractAIAgentRepository:
        return RelationalDBAIAgentRepository(session, llm_factory)

    @provider
    def provide_pokemon_unit_of_work(
        self, 
        session: AsyncSession, 
        pokemon_repo: RelationalDBPokemonRepository,
    ) -> AbstractPokemonUnitOfWork:
        return RelationalPokemonUnitOfWork(session, pokemon_repo)

    @provider
    def provide_ai_agent_unit_of_work(
        self, 
        session: AsyncSession, 
        ai_agent_repo: AbstractAIAgentRepository,
    ) -> AbstractAIAgentUnitOfWork:
        return RelationalAIAgentUnitOfWork(session, ai_agent_repo)

    @provider
    def provide_async_sqlalchemy_unit_of_work(
        self, 
        session: AsyncSession, 
        pokemon_repo: RelationalDBPokemonRepository,
        ai_agent_repo: AbstractAIAgentRepository,
    ) -> AbstractUnitOfWork:
        return AsyncSQLAlchemyUnitOfWork(session, pokemon_repo, ai_agent_repo)


class DocumentDBModule(Module):
    @singleton
    @provider
    def provide_async_mongo_collection(
        self,
    ) -> AsyncIOMotorCollection:  # pyright: ignore[reportInvalidTypeForm]
        from settings.db.mongodb import COLLECTION_NAME, DATABASE_NAME, AsyncMongoDBEngine

        return AsyncMongoDBEngine[DATABASE_NAME][COLLECTION_NAME]

    @provider
    def provide_pokemon_repository(
        self,
        collection: AsyncIOMotorCollection,  # pyright: ignore[reportInvalidTypeForm]
    ) -> MongoDBPokemonRepository:
        return MongoDBPokemonRepository(collection, session=None)

    @provider
    def provide_ai_agent_repository(
        self,
        collection: AsyncIOMotorCollection,  # pyright: ignore[reportInvalidTypeForm]
        llm_factory: LLMFactory,
    ) -> AbstractAIAgentRepository:
        return MongoDBAIAgentRepository(collection, llm_factory)

    @provider
    def provide_pokemon_unit_of_work(
        self,
        pokemon_repo: MongoDBPokemonRepository,
    ) -> AbstractPokemonUnitOfWork:
        from settings.db.mongodb import AsyncMongoDBEngine
        return MongoDBPokemonUnitOfWork(AsyncMongoDBEngine, pokemon_repo)

    @provider
    def provide_ai_agent_unit_of_work(
        self,
        ai_agent_repo: AbstractAIAgentRepository,
    ) -> AbstractAIAgentUnitOfWork:
        from settings.db.mongodb import AsyncMongoDBEngine
        return MongoDBAIAgentUnitOfWork(AsyncMongoDBEngine, ai_agent_repo)

    @provider
    def provide_async_motor_unit_of_work(
        self, pokemon_repo: MongoDBPokemonRepository, ai_agent_repo: AbstractAIAgentRepository
    ) -> AbstractUnitOfWork:
        from settings.db.mongodb import AsyncMongoDBEngine

        return AsyncMotorUnitOfWork(AsyncMongoDBEngine, pokemon_repo, ai_agent_repo)


class KeyValueDBModule(Module):
    @provider
    def provide_async_redis_client(self) -> AsyncRedis:
        from settings.db import get_async_client
        return get_async_client()

    @provider
    def provide_pokemon_repository(self, client) -> RedisPokemonRepository:
        return RedisPokemonRepository(client)

    @provider
    def provide_ai_agent_repository(self, client, llm_factory: LLMFactory) -> AbstractAIAgentRepository:
        return RedisAIAgentRepository(client, llm_factory)

    @provider
    def provide_pokemon_unit_of_work(self, client, pokemon_repo: RedisPokemonRepository) -> AbstractPokemonUnitOfWork:
        return RedisPokemonUnitOfWork(client, pokemon_repo)

    @provider
    def provide_ai_agent_unit_of_work(self, client, ai_agent_repo: AbstractAIAgentRepository) -> AbstractAIAgentUnitOfWork:
        return RedisAIAgentUnitOfWork(client, ai_agent_repo)

    @provider
    def provide_async_redis_unit_of_work(self, client, pokemon_repo: RedisPokemonRepository, ai_agent_repo: AbstractAIAgentRepository) -> AbstractUnitOfWork:
        return AsyncRedisUnitOfWork(client, pokemon_repo, ai_agent_repo)


class DatabaseModuleFactory:
    def create_module(self):
        if IS_RELATIONAL_DB:
            return RelationalDBModule()
        if IS_DOCUMENT_DB:
            return DocumentDBModule()
        if IS_KEY_VALUE_DB:
            return KeyValueDBModule()

        raise RuntimeError(
            'Invalid database type configuration. It\'s neither relational nor NoSQL'
        )


injector = Injector([DatabaseModuleFactory().create_module(), LLMModule()])
