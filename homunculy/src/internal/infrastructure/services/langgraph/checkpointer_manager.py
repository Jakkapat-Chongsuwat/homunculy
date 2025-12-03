"""
Checkpointer management for LangGraph.

Handles PostgreSQL and in-memory checkpoint initialization.
"""

import asyncio
import os
from typing import Any, Optional

from common.logger import get_logger
from internal.infrastructure.services.langgraph.exceptions import (
    CheckpointerConnectionException,
    CheckpointerSetupException,
)
from settings import DATABASE_URI


logger = get_logger(__name__)


# Try importing PostgreSQL checkpointer
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool

    HAS_POSTGRES_CHECKPOINT = True
except ImportError:
    HAS_POSTGRES_CHECKPOINT = False
    AsyncPostgresSaver = None
    AsyncConnectionPool = None


class CheckpointerManager:
    """
    Manages LangGraph checkpointer initialization and lifecycle.

    Supports:
    - PostgreSQL (production) via AsyncPostgresSaver
    - In-memory (development/testing) via MemorySaver
    """

    def __init__(self, checkpointer: Optional[Any] = None) -> None:
        """
        Initialize checkpointer manager.

        Args:
            checkpointer: Pre-configured checkpointer (for testing)
        """
        self._checkpointer = checkpointer
        self._initialized = checkpointer is not None
        self._postgres_pool: Optional[Any] = None

    @property
    def checkpointer(self) -> Any:
        """Get current checkpointer instance."""
        return self._checkpointer

    @property
    def is_initialized(self) -> bool:
        """Check if checkpointer is ready."""
        return self._initialized

    @property
    def storage_type(self) -> str:
        """Get current storage type."""
        if not self._checkpointer:
            return "none"
        name = type(self._checkpointer).__name__
        if name == "AsyncPostgresSaver":
            return "postgres"
        return "memory"

    async def ensure_initialized(self) -> None:
        """Initialize checkpointer on first use."""
        if self._initialized:
            return

        logger.info("Initializing checkpointer")

        if self._should_use_postgres():
            await self._init_postgres()
        else:
            self._init_memory()

        self._initialized = True
        logger.info(
            "Checkpointer ready",
            type=type(self._checkpointer).__name__,
        )

    def _should_use_postgres(self) -> bool:
        """Check if PostgreSQL should be used."""
        return HAS_POSTGRES_CHECKPOINT and bool(DATABASE_URI)

    async def _init_postgres(self) -> None:
        """Initialize PostgreSQL checkpointer."""
        if not HAS_POSTGRES_CHECKPOINT or AsyncPostgresSaver is None or AsyncConnectionPool is None:
            raise CheckpointerSetupException(
                "PostgreSQL checkpointer package not installed",
                storage_type="postgres",
            )

        db_uri = DATABASE_URI.replace('+asyncpg', '')
        db_host = self._extract_host(db_uri)

        logger.info("Connecting to Postgres", db_host=db_host)

        try:
            self._postgres_pool = AsyncConnectionPool(
                db_uri,
                min_size=2,
                max_size=10,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": 0,
                    "row_factory": dict_row,
                },
            )

            self._checkpointer = AsyncPostgresSaver(self._postgres_pool)

            await asyncio.wait_for(
                self._checkpointer.setup(),
                timeout=30.0,
            )

            logger.info("PostgreSQL checkpointer initialized")

        except asyncio.TimeoutError as e:
            raise CheckpointerConnectionException(
                "PostgreSQL connection timed out",
                storage_type="postgres",
            ) from e
        except Exception as e:
            raise CheckpointerSetupException(
                f"PostgreSQL setup failed: {e}",
                storage_type="postgres",
            ) from e

    def _init_memory(self) -> None:
        """Initialize in-memory checkpointer."""
        from langgraph.checkpoint.memory import MemorySaver

        reason = "package not installed" if not HAS_POSTGRES_CHECKPOINT else "no DATABASE_URI"
        logger.warning("Using MemorySaver", reason=reason)

        self._checkpointer = MemorySaver()

    def _extract_host(self, db_uri: str) -> str:
        """Extract host from database URI."""
        if '@' in db_uri:
            return db_uri.split('@')[1].split('/')[0]
        return "unknown"

    async def cleanup(self) -> None:
        """Release checkpointer resources."""
        if self._postgres_pool:
            try:
                await self._postgres_pool.close()
                logger.info("PostgreSQL pool closed")
            except Exception as e:
                logger.error("Pool close error", error=str(e))


def create_checkpointer_manager(
    checkpointer: Optional[Any] = None,
) -> CheckpointerManager:
    """Factory function for CheckpointerManager."""
    return CheckpointerManager(checkpointer=checkpointer)
