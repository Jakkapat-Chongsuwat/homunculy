"""In-memory store adapter for testing and development."""

from datetime import datetime

from common.logger import get_logger
from domain.interfaces.store import StoreItem, StorePort, StoreQuery

logger = get_logger(__name__)


class InMemoryStoreAdapter(StorePort):
    """In-memory implementation of StorePort."""

    def __init__(self) -> None:
        self._store: dict[tuple, dict[str, StoreItem]] = {}
        logger.info("InMemoryStore initialized")

    async def put(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict,
    ) -> None:
        """Store value at namespace+key."""
        item = _create_item(namespace, key, value)
        _ensure_namespace(self._store, namespace)
        _update_store(self._store, namespace, key, item)
        logger.debug("Stored item", namespace=namespace, key=key)

    async def get(
        self,
        namespace: tuple[str, ...],
        key: str,
    ) -> StoreItem | None:
        """Get value by namespace+key."""
        return _find_item(self._store, namespace, key)

    async def search(self, query: StoreQuery) -> list[StoreItem]:
        """Search items in namespace."""
        items = _get_namespace_items(self._store, query.namespace)
        filtered = _apply_filter(items, query.filter_dict)
        return _limit_results(filtered, query.limit)

    async def delete(
        self,
        namespace: tuple[str, ...],
        key: str,
    ) -> bool:
        """Delete item by namespace+key."""
        return _remove_item(self._store, namespace, key)


def _create_item(
    namespace: tuple[str, ...],
    key: str,
    value: dict,
) -> StoreItem:
    """Create new store item."""
    now = datetime.now()
    return StoreItem(
        namespace=namespace,
        key=key,
        value=value,
        created_at=now,
        updated_at=now,
    )


def _ensure_namespace(store: dict, namespace: tuple[str, ...]) -> None:
    """Ensure namespace exists in store."""
    if namespace not in store:
        store[namespace] = {}


def _update_store(
    store: dict,
    namespace: tuple[str, ...],
    key: str,
    item: StoreItem,
) -> None:
    """Update item in store."""
    existing = store[namespace].get(key)
    if existing:
        item.created_at = existing.created_at
    store[namespace][key] = item


def _find_item(
    store: dict,
    namespace: tuple[str, ...],
    key: str,
) -> StoreItem | None:
    """Find item in store."""
    ns_dict = store.get(namespace, {})
    return ns_dict.get(key)


def _get_namespace_items(
    store: dict,
    namespace: tuple[str, ...],
) -> list[StoreItem]:
    """Get all items in namespace."""
    ns_dict = store.get(namespace, {})
    return list(ns_dict.values())


def _apply_filter(
    items: list[StoreItem],
    filter_dict: dict | None,
) -> list[StoreItem]:
    """Filter items by criteria."""
    if not filter_dict:
        return items
    return [i for i in items if _matches_filter(i, filter_dict)]


def _matches_filter(item: StoreItem, filter_dict: dict) -> bool:
    """Check if item matches filter."""
    for key, val in filter_dict.items():
        if item.value.get(key) != val:
            return False
    return True


def _limit_results(items: list[StoreItem], limit: int) -> list[StoreItem]:
    """Limit number of results."""
    return items[:limit]


def _remove_item(
    store: dict,
    namespace: tuple[str, ...],
    key: str,
) -> bool:
    """Remove item from store."""
    ns_dict = store.get(namespace, {})
    if key in ns_dict:
        del ns_dict[key]
        return True
    return False
