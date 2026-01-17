"""Checkpointer management for LangGraph state persistence.

Uses Unit of Work pattern with proper encapsulation.
No global state - fully thread-safe and testable.
"""

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from common.logger import get_logger
from langgraph.checkpoint.memory import MemorySaver

logger = get_logger(__name__)


class CheckpointerUnitOfWork:
    """
    Unit of Work for checkpointer lifecycle management.

    Manages connection lifecycle via async context manager.
    No global state - fully thread-safe and testable.
    """

    def __init__(self) -> None:
        self._context: Any = None
        self._checkpointer: Any = None
        self._initialized = False

    @property
    def checkpointer(self) -> Any:
        """Get the checkpointer instance."""
        return self._checkpointer

    @property
    def storage_type(self) -> str:
        """Get storage type name."""
        if not self._checkpointer:
            return "none"
        return type(self._checkpointer).__name__

    @property
    def is_initialized(self) -> bool:
        """Check if checkpointer is initialized."""
        return self._initialized

    def set_context(self, context: Any) -> None:
        """Set the async context manager (for internal use by factory)."""
        self._context = context

    def set_checkpointer(self, checkpointer: Any) -> None:
        """Set the checkpointer instance (for internal use by factory)."""
        self._checkpointer = checkpointer

    async def setup(self) -> None:
        """Run checkpointer setup (create tables, etc)."""
        if self._initialized:
            return
        if hasattr(self._checkpointer, "setup"):
            await self._checkpointer.setup()
        self._initialized = True
        logger.info("Checkpointer initialized", type=self.storage_type)

    async def cleanup(self) -> None:
        """Cleanup checkpointer resources."""
        if self._context:
            await self._context.__aexit__(None, None, None)
            self._context = None
            self._checkpointer = None
            self._initialized = False
        logger.info("Checkpointer cleaned up")


class CheckpointerFactory:
    """Factory for creating checkpointer UoW instances."""

    @staticmethod
    async def create_postgres(conn_string: str) -> CheckpointerUnitOfWork:
        """Create PostgreSQL checkpointer UoW."""
        uow = CheckpointerUnitOfWork()
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            context = AsyncPostgresSaver.from_conn_string(conn_string)
            checkpointer = await context.__aenter__()
            uow.set_context(context)
            uow.set_checkpointer(checkpointer)
            logger.info("PostgreSQL checkpointer created")
        except ImportError:
            logger.warning("PostgreSQL not available, using memory")
            uow.set_checkpointer(MemorySaver())
        except Exception as exc:
            logger.error("PostgreSQL failed, using memory", error=str(exc))
            uow.set_checkpointer(MemorySaver())
        return uow

    @staticmethod
    def create_memory() -> CheckpointerUnitOfWork:
        """Create in-memory checkpointer UoW."""
        uow = CheckpointerUnitOfWork()
        uow.set_checkpointer(MemorySaver())
        logger.info("Memory checkpointer created")
        return uow


@asynccontextmanager
async def postgres_checkpointer_context() -> AsyncIterator[CheckpointerUnitOfWork]:
    """
    Async context manager for PostgreSQL checkpointer.

    Usage:
        async with postgres_checkpointer_context() as uow:
            await uow.setup()
            graph = build_graph(checkpointer=uow.checkpointer)
        # cleanup is automatic
    """
    conn_string = _postgres_connection_string()
    uow = await CheckpointerFactory.create_postgres(conn_string)
    try:
        yield uow
    finally:
        await uow.cleanup()


@asynccontextmanager
async def memory_checkpointer_context() -> AsyncIterator[CheckpointerUnitOfWork]:
    """
    Async context manager for in-memory checkpointer.

    Useful for testing and development.
    """
    uow = CheckpointerFactory.create_memory()
    try:
        yield uow
    finally:
        await uow.cleanup()


def _postgres_connection_string() -> str:
    """Build PostgreSQL connection string from environment."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "homunculy")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"
