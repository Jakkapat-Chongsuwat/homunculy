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
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository
from repositories.relational_db.ai_agent.repository import RelationalDBAIAgentRepository
from repositories.relational_db.waifu.repository import RelationalDBWaifuRepository
from repositories.abstraction.ai_agent import AbstractAIAgentRepository
from repositories.abstraction.waifu import AbstractWaifuRepository
from repositories.abstraction.llm import ILLMFactory
from repositories.llm_service.llm_factory import LLMFactory
from settings.db import IS_DOCUMENT_DB, IS_RELATIONAL_DB

from .unit_of_work import (
    AsyncSQLAlchemyUnitOfWork,
    AbstractAIAgentUnitOfWork,
    RelationalAIAgentUnitOfWork,
    MongoDBAIAgentUnitOfWork,
)


class LLMModule(Module):
    """Module for LLM service dependencies."""

    @singleton
    @provider
    def provide_llm_factory(self) -> ILLMFactory:
        """
        Provides the LLM factory for creating LLM clients.
        
        Returns the interface (ILLMFactory) to follow Dependency Inversion Principle.
        The concrete implementation (LLMFactory) is created here but returned as interface.
        """
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
    def provide_ai_agent_repository(self, session: AsyncSession, llm_factory: ILLMFactory) -> AbstractAIAgentRepository:
        return RelationalDBAIAgentRepository(session, llm_factory)

    @provider
    def provide_waifu_repository(self, session: AsyncSession) -> AbstractWaifuRepository:
        return RelationalDBWaifuRepository(session)


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
        ai_agent_repo: AbstractAIAgentRepository,
    ) -> AbstractAIAgentUnitOfWork:
        return AsyncSQLAlchemyUnitOfWork(session, ai_agent_repo)


class DocumentDBModule(Module):
    @singleton
    @provider
    def provide_async_mongo_collection(
        self,
    ) -> AsyncIOMotorCollection:  # pyright: ignore[reportInvalidTypeForm]
        from settings.db.mongodb import COLLECTION_NAME, DATABASE_NAME, AsyncMongoDBEngine

        return AsyncMongoDBEngine[DATABASE_NAME][COLLECTION_NAME]

    @provider
    def provide_ai_agent_repository(
        self,
        collection: AsyncIOMotorCollection,  # pyright: ignore[reportInvalidTypeForm]
        llm_factory: ILLMFactory,
    ) -> AbstractAIAgentRepository:
        return MongoDBAIAgentRepository(collection, llm_factory)

    @provider
    def provide_ai_agent_unit_of_work(
        self,
        ai_agent_repo: AbstractAIAgentRepository,
    ) -> AbstractAIAgentUnitOfWork:
        from settings.db.mongodb import AsyncMongoDBEngine
        return MongoDBAIAgentUnitOfWork(AsyncMongoDBEngine, ai_agent_repo)

    @provider
    def provide_async_motor_unit_of_work(
        self, ai_agent_repo: AbstractAIAgentRepository
    ) -> AbstractAIAgentUnitOfWork:
        from settings.db.mongodb import AsyncMongoDBEngine
        # AsyncMotorUnitOfWork implementation was removed; return the
        # MongoDB-backed UoW which provides equivalent per-message
        # transactional semantics for now.
        return MongoDBAIAgentUnitOfWork(AsyncMongoDBEngine, ai_agent_repo)


# Key-value / Redis support removed for now. If needed in the future,
# reintroduce a KeyValueDBModule that provides a Redis client, repository
# and UoW implementations. For now we intentionally avoid wiring Redis.


class DatabaseModuleFactory:
    def create_module(self):
        if IS_RELATIONAL_DB:
            return RelationalDBModule()
        if IS_DOCUMENT_DB:
            return DocumentDBModule()
        # Key-value DB (Redis) is not supported in this configuration.
        raise RuntimeError(
            "Invalid database type configuration: must set one of IS_RELATIONAL_DB or IS_DOCUMENT_DB"
        )


injector = Injector([DatabaseModuleFactory().create_module(), LLMModule()])
