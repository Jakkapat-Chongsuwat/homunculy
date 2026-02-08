"""Checkpointer factory for creating instances."""

from langgraph.checkpoint.memory import MemorySaver

from common.logger import get_logger
from infrastructure.persistence.checkpointer.manager import CheckpointerUnitOfWork

logger = get_logger(__name__)


class CheckpointerFactory:
    """Factory for creating checkpointer instances."""

    @staticmethod
    async def create_postgres(conn: str) -> CheckpointerUnitOfWork:
        """Create PostgreSQL checkpointer."""
        uow = CheckpointerUnitOfWork()
        try:
            checkpointer = await _create_postgres_saver(conn)
            context = checkpointer[0]
            saver = checkpointer[1]
            uow.set_context(context)
            uow.set_checkpointer(saver)
            logger.info("PostgreSQL checkpointer created")
        except ImportError:
            _fallback_to_memory(uow, "PostgreSQL not available")
        except Exception as exc:
            _fallback_to_memory(uow, f"PostgreSQL failed: {exc}")
        return uow

    @staticmethod
    def create_memory() -> CheckpointerUnitOfWork:
        """Create in-memory checkpointer."""
        uow = CheckpointerUnitOfWork()
        uow.set_checkpointer(MemorySaver())
        logger.info("Memory checkpointer created")
        return uow


async def _create_postgres_saver(conn: str) -> tuple:
    """Create PostgreSQL saver with context."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    context = AsyncPostgresSaver.from_conn_string(conn)
    saver = await context.__aenter__()
    return (context, saver)


def _fallback_to_memory(uow: CheckpointerUnitOfWork, reason: str) -> None:
    """Fallback to memory checkpointer."""
    logger.warning(reason, fallback="memory")
    uow.set_checkpointer(MemorySaver())
