"""Checkpointer management for LangGraph state persistence."""

import os
from typing import Any

from common.logger import get_logger
from langgraph.checkpoint.memory import MemorySaver

logger = get_logger(__name__)


class CheckpointerManager:
    """Manages checkpointer lifecycle."""

    def __init__(self, checkpointer: Any = None) -> None:
        self._checkpointer = checkpointer
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

    async def ensure_initialized(self) -> None:
        """Ensure checkpointer is initialized."""
        if self._initialized:
            return
        if hasattr(self._checkpointer, "setup"):
            await self._checkpointer.setup()
        self._initialized = True
        logger.info("Checkpointer initialized", type=self.storage_type)

    async def cleanup(self) -> None:
        """Cleanup checkpointer resources."""
        if not self._checkpointer:
            return
        if hasattr(self._checkpointer, "cleanup"):
            await self._checkpointer.cleanup()
        logger.info("Checkpointer cleaned up")


async def create_postgres_checkpointer() -> Any:
    """Create PostgreSQL checkpointer from environment."""
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        conn_string = _postgres_connection_string()
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            await checkpointer.setup()
            logger.info("PostgreSQL checkpointer created")
            return checkpointer
    except ImportError:
        logger.warning("PostgreSQL checkpointer not available")
        return MemorySaver()
    except Exception as exc:
        logger.error("Failed to create PostgreSQL checkpointer", error=str(exc))
        return MemorySaver()


def create_memory_checkpointer() -> MemorySaver:
    """Create in-memory checkpointer."""
    return MemorySaver()


def _postgres_connection_string() -> str:
    """Build PostgreSQL connection string from environment."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "homunculy")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"
