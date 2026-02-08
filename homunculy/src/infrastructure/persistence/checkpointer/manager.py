"""Checkpointer Unit of Work for lifecycle management."""

from typing import Any

from common.logger import get_logger

logger = get_logger(__name__)


class CheckpointerUnitOfWork:
    """Unit of Work for checkpointer lifecycle."""

    def __init__(self) -> None:
        self._context: Any = None
        self._checkpointer: Any = None
        self._initialized = False

    @property
    def checkpointer(self) -> Any:
        """Get checkpointer instance."""
        return self._checkpointer

    @property
    def storage_type(self) -> str:
        """Get storage type name."""
        if not self._checkpointer:
            return "none"
        return type(self._checkpointer).__name__

    @property
    def is_initialized(self) -> bool:
        """Check initialization status."""
        return self._initialized

    def set_context(self, context: Any) -> None:
        """Set async context manager."""
        self._context = context

    def set_checkpointer(self, checkpointer: Any) -> None:
        """Set checkpointer instance."""
        self._checkpointer = checkpointer

    async def setup(self) -> None:
        """Initialize checkpointer."""
        if self._initialized:
            return
        await _setup_checkpointer(self._checkpointer)
        self._initialized = True
        logger.info("Checkpointer initialized", type=self.storage_type)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await _cleanup_context(self._context)
        self._context = None
        self._checkpointer = None
        self._initialized = False
        logger.info("Checkpointer cleaned up")


async def _setup_checkpointer(checkpointer: Any) -> None:
    """Run checkpointer setup if available."""
    if hasattr(checkpointer, "setup"):
        await checkpointer.setup()


async def _cleanup_context(context: Any) -> None:
    """Cleanup async context."""
    if context:
        await context.__aexit__(None, None, None)
