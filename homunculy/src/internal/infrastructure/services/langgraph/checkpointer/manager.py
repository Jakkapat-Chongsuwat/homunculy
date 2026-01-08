"""
Checkpointer management for LangGraph.

Handles PostgreSQL and in-memory checkpoint initialization.
"""

import asyncio
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
    """Manages LangGraph checkpointer initialization and lifecycle."""

    def __init__(self, checkpointer: Optional[Any] = None) -> None:
        self._checkpointer = checkpointer
        self._initialized = checkpointer is not None
        self._postgres_pool: Optional[Any] = None

    @property
    def checkpointer(self) -> Any:
        return self._checkpointer

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def storage_type(self) -> str:
        if not self._checkpointer:
            return "none"
        name = type(self._checkpointer).__name__
        return "postgres" if name == "AsyncPostgresSaver" else "memory"

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
        logger.info("Checkpointer ready", type=type(self._checkpointer).__name__)

    def _should_use_postgres(self) -> bool:
        return HAS_POSTGRES_CHECKPOINT and bool(DATABASE_URI)

    async def _init_postgres(self) -> None:
        """Initialize PostgreSQL checkpointer."""
        if not HAS_POSTGRES_CHECKPOINT or not AsyncPostgresSaver or not AsyncConnectionPool:
            raise CheckpointerSetupException(
                "PostgreSQL checkpointer package not installed",
                storage_type="postgres",
            )

        db_uri = DATABASE_URI.replace('+asyncpg', '')
        db_uri = self._to_psycopg_uri(db_uri)
        logger.info("Connecting to Postgres", db_host=self._extract_host(db_uri))

        try:
            self._postgres_pool = AsyncConnectionPool(
                db_uri,
                min_size=2,
                max_size=10,
                kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            )
            self._checkpointer = AsyncPostgresSaver(self._postgres_pool)
            await asyncio.wait_for(self._checkpointer.setup(), timeout=30.0)
            logger.info("PostgreSQL checkpointer initialized")

        except asyncio.TimeoutError as e:
            raise CheckpointerConnectionException(
                "PostgreSQL connection timed out", storage_type="postgres"
            ) from e
        except Exception as e:
            raise CheckpointerSetupException(
                f"PostgreSQL setup failed: {e}", storage_type="postgres"
            ) from e

    def _init_memory(self) -> None:
        """Initialize in-memory checkpointer."""
        from langgraph.checkpoint.memory import MemorySaver

        reason = "package not installed" if not HAS_POSTGRES_CHECKPOINT else "no DATABASE_URI"
        logger.warning("Using MemorySaver", reason=reason)
        self._checkpointer = MemorySaver()

    def _extract_host(self, db_uri: str) -> str:
        return db_uri.split('@')[1].split('/')[0] if '@' in db_uri else "unknown"

    def _to_psycopg_uri(self, db_uri: str) -> str:
        """Convert a SQLAlchemy/asyncpg-style URI into a psycopg-compatible URI.

        Today we primarily need to translate the query parameter `ssl` -> `sslmode`.
        psycopg rejects `ssl=...` while asyncpg rejects `sslmode=...`.
        """
        parts = urlsplit(db_uri)
        if not parts.query:
            return db_uri

        query_pairs = parse_qsl(parts.query, keep_blank_values=True)
        rewritten: list[tuple[str, str]] = []
        for key, value in query_pairs:
            if key == "ssl":
                rewritten.append(("sslmode", value))
            else:
                rewritten.append((key, value))

        new_query = urlencode(rewritten)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    async def cleanup(self) -> None:
        """Release checkpointer resources."""
        if self._postgres_pool:
            try:
                await self._postgres_pool.close()
                logger.info("PostgreSQL pool closed")
            except Exception as e:
                logger.error("Pool close error", error=str(e))


def create_checkpointer_manager(checkpointer: Optional[Any] = None) -> CheckpointerManager:
    """Factory function for CheckpointerManager."""
    return CheckpointerManager(checkpointer=checkpointer)
