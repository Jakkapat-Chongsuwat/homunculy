"""Context managers for checkpointer lifecycle."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from infrastructure.persistence.checkpointer.factory import CheckpointerFactory
from infrastructure.persistence.checkpointer.manager import CheckpointerUnitOfWork


@asynccontextmanager
async def postgres_checkpointer() -> AsyncIterator[CheckpointerUnitOfWork]:
    """PostgreSQL checkpointer context."""
    conn = _build_connection_string()
    uow = await CheckpointerFactory.create_postgres(conn)
    try:
        yield uow
    finally:
        await uow.cleanup()


@asynccontextmanager
async def memory_checkpointer() -> AsyncIterator[CheckpointerUnitOfWork]:
    """Memory checkpointer context."""
    uow = CheckpointerFactory.create_memory()
    try:
        yield uow
    finally:
        await uow.cleanup()


def _build_connection_string() -> str:
    """Build PostgreSQL connection string."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "homunculy")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"
