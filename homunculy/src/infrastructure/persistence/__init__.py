"""Persistence infrastructure - Database and checkpointers."""

from infrastructure.persistence.checkpointer import (
    CheckpointerFactory,
    CheckpointerManager,
    CheckpointerUnitOfWork,
    create_memory_checkpointer,
    create_postgres_checkpointer,
    memory_checkpointer_context,
    postgres_checkpointer_context,
)

__all__ = [
    # New UoW pattern (recommended)
    "CheckpointerUnitOfWork",
    "CheckpointerFactory",
    "postgres_checkpointer_context",
    "memory_checkpointer_context",
    # Legacy (deprecated)
    "CheckpointerManager",
    "create_postgres_checkpointer",
    "create_memory_checkpointer",
]
