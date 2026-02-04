"""Memory Port - Long-term memory for companion.

Abstracts memory storage and retrieval for the companion.
Supports semantic search, episodic memory, and user preferences.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryType(Enum):
    """Types of memories."""

    EPISODIC = "episodic"  # Specific events/conversations
    SEMANTIC = "semantic"  # Facts and knowledge
    PREFERENCE = "preference"  # User preferences
    RELATIONSHIP = "relationship"  # Relationship context


@dataclass
class Memory:
    """A single memory entry."""

    id: str
    content: str
    memory_type: MemoryType
    importance: float = 0.5  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryQuery:
    """Query for retrieving memories."""

    query: str
    user_id: str
    memory_types: list[MemoryType] | None = None
    limit: int = 5
    min_importance: float = 0.0


@dataclass
class MemoryResult:
    """Result from memory search."""

    memories: list[Memory]
    total_found: int


class MemoryPort(ABC):
    """Memory storage and retrieval contract."""

    @abstractmethod
    async def store(self, user_id: str, memory: Memory) -> str:
        """Store a memory, return ID."""
        ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> MemoryResult:
        """Search memories semantically."""
        ...

    @abstractmethod
    async def get_recent(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[Memory]:
        """Get recent memories for user."""
        ...

    @abstractmethod
    async def get_by_type(
        self,
        user_id: str,
        memory_type: MemoryType,
        limit: int = 10,
    ) -> list[Memory]:
        """Get memories by type."""
        ...

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        ...

    async def close(self) -> None:
        """Close resources. Override if needed."""
        pass
