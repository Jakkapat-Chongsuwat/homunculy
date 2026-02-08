"""Memory service for LangGraph Store integration.

Implements get_memory and update_memory patterns from LangGraph docs.
Handles user preferences, session context, and learning from feedback.
"""

from common.logger import get_logger
from domain.interfaces.store import StorePort

logger = get_logger(__name__)


class MemoryService:
    """Memory management service."""

    def __init__(self, store: StorePort) -> None:
        self._store = store
        logger.info("MemoryService initialized")

    def get_memory(
        self,
        namespace: tuple[str, ...],
        key: str,
        default: str | None = None,
    ) -> str | None:
        """Get memory or initialize with default."""
        item = self._store.get(namespace, key)
        if item:
            return _extract_value(item)
        return _init_default(self._store, namespace, key, default)

    def update_memory(
        self,
        namespace: tuple[str, ...],
        key: str,
        content: str,
    ) -> None:
        """Update memory with new content."""
        _store_content(self._store, namespace, key, content)
        logger.debug("Updated memory", namespace=namespace, key=key)

    def search_memories(
        self,
        namespace: tuple[str, ...],
        limit: int = 10,
    ) -> list[str]:
        """Search memories in namespace."""
        items = self._store.search(namespace, limit=limit)
        return _extract_values(items)


def _init_default(
    store: StorePort,
    namespace: tuple[str, ...],
    key: str,
    default: str | None,
) -> str | None:
    """Initialize memory with default value."""
    if default is None:
        return None
    _store_content(store, namespace, key, default)
    return default


def _store_content(
    store: StorePort,
    namespace: tuple[str, ...],
    key: str,
    content: str,
) -> None:
    """Store content in memory."""
    value = {"content": content}
    store.put(namespace, key, value)


def _extract_value(item) -> str:
    """Extract content from store item."""
    return item.value.get("content", "")


def _extract_values(items: list) -> list[str]:
    """Extract content from multiple items."""
    return [_extract_value(i) for i in items]
