"""In-memory store adapter for testing and development.

Extends LangGraph BaseStore for InjectedStore compatibility.
Thin wrapper over dict with namespace isolation.
"""

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
)

from common.logger import get_logger

logger = get_logger(__name__)


class InMemoryStoreAdapter(BaseStore):
    """In-memory BaseStore for testing."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, ...], dict[str, Item]] = {}
        logger.info("InMemoryStore initialized")

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Dispatch operations synchronously."""
        return [_dispatch(self._data, op) for op in ops]

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Dispatch operations asynchronously (wraps sync)."""
        return self.batch(ops)


# --- Op dispatching ---


def _dispatch(
    data: dict[tuple[str, ...], dict[str, Item]],
    op: Op,
) -> Result:
    """Route operation to handler."""
    if isinstance(op, GetOp):
        return _handle_get(data, op)
    if isinstance(op, SearchOp):
        return _handle_search(data, op)
    if isinstance(op, PutOp):
        return _handle_put(data, op)
    if isinstance(op, ListNamespacesOp):
        return _handle_list(data, op)
    msg = f"Unknown op type: {type(op)}"
    raise ValueError(msg)


def _handle_get(
    data: dict[tuple[str, ...], dict[str, Item]],
    op: GetOp,
) -> Item | None:
    """Get item by namespace + key."""
    return data.get(op.namespace, {}).get(op.key)


def _handle_search(
    data: dict[tuple[str, ...], dict[str, Item]],
    op: SearchOp,
) -> list[SearchItem]:
    """Search with namespace prefix matching."""
    items = _collect_prefix(data, op.namespace_prefix)
    filtered = _apply_filter(items, op.filter)
    return filtered[op.offset : op.offset + op.limit]


def _handle_put(
    data: dict[tuple[str, ...], dict[str, Item]],
    op: PutOp,
) -> None:
    """Put or delete item."""
    try:
        if op.value is None:
            data.get(op.namespace, {}).pop(op.key, None)
        else:
            _upsert(data, op.namespace, op.key, op.value)
    except Exception as e:
        logger.error("Failed to put item", error=str(e))
        raise


def _handle_list(
    data: dict[tuple[str, ...], dict[str, Item]],
    op: ListNamespacesOp,
) -> list[tuple[str, ...]]:
    """List distinct namespaces."""
    namespaces = list(data.keys())
    if op.max_depth is not None:
        namespaces = [ns for ns in namespaces if len(ns) <= op.max_depth]
    return namespaces[op.offset : op.offset + op.limit]


# --- Helpers ---


def _upsert(
    data: dict[tuple[str, ...], dict[str, Item]],
    namespace: tuple[str, ...],
    key: str,
    value: dict[str, Any],
) -> None:
    """Insert or update item."""
    now = datetime.now()
    ns_dict = data.setdefault(namespace, {})
    created = ns_dict[key].created_at if key in ns_dict else now
    ns_dict[key] = Item(
        value=value,
        key=key,
        namespace=namespace,
        created_at=created,
        updated_at=now,
    )


def _collect_prefix(
    data: dict[tuple[str, ...], dict[str, Item]],
    prefix: tuple[str, ...],
) -> list[SearchItem]:
    """Collect items from namespaces matching prefix."""
    items: list[SearchItem] = []
    for ns, ns_dict in data.items():
        if ns[: len(prefix)] == prefix:
            items.extend(_to_search_items(ns_dict))
    return items


def _to_search_items(ns_dict: dict[str, Item]) -> list[SearchItem]:
    """Convert namespace items to SearchItems."""
    return [
        SearchItem(
            value=item.value,
            key=item.key,
            namespace=item.namespace,
            created_at=item.created_at,
            updated_at=item.updated_at,
            score=0.0,
        )
        for item in ns_dict.values()
    ]


def _apply_filter(
    items: list[SearchItem],
    filter_dict: dict[str, Any] | None,
) -> list[SearchItem]:
    """Apply key-value filter on items."""
    if not filter_dict:
        return items
    return [i for i in items if _matches(i, filter_dict)]


def _matches(item: SearchItem, criteria: dict[str, Any]) -> bool:
    """Check item value matches all criteria."""
    return all(item.value.get(k) == v for k, v in criteria.items())
