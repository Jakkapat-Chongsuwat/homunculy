"""Store Port - LangGraph cross-thread memory storage.

Follows LangGraph Store pattern for long-term memory.
Namespaces organize memories by tenant/user/category.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class StoreItem:
    """Item stored in memory store."""

    namespace: tuple[str, ...]
    key: str
    value: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class StoreQuery:
    """Query for searching store items."""

    namespace: tuple[str, ...]
    filter_dict: dict[str, Any] | None = None
    limit: int = 10


class StorePort(ABC):
    """Long-term memory store contract."""

    @abstractmethod
    async def put(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
    ) -> None:
        """Store value at namespace+key."""
        ...

    @abstractmethod
    async def get(
        self,
        namespace: tuple[str, ...],
        key: str,
    ) -> StoreItem | None:
        """Get value by namespace+key."""
        ...

    @abstractmethod
    async def search(self, query: StoreQuery) -> list[StoreItem]:
        """Search items in namespace."""
        ...

    @abstractmethod
    async def delete(
        self,
        namespace: tuple[str, ...],
        key: str,
    ) -> bool:
        """Delete item by namespace+key."""
        ...
