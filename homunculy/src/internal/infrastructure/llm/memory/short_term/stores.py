"""Storage utilities for short-term and summary memory."""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List

from .models import MemoryConfig, MemoryMessage, SummaryEntry


class ShortTermMemoryStore:
    """Bounded, TTL-aware in-memory store for conversational context."""

    def __init__(self, config: MemoryConfig | None = None) -> None:
        self._config = config or MemoryConfig()
        self._messages: Dict[str, Deque[MemoryMessage]] = {}
        self._counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def read(self, key: str) -> List[Dict[str, str]]:
        """Return non-expired messages for the provided key."""

        async with self._lock:
            queue = self._messages.get(key)
            if not queue:
                return []

            self._prune(queue)
            return [
                {"role": entry["role"], "content": entry["content"]}
                for entry in queue
            ]

    async def append(self, key: str, role: str, content: str) -> None:
        """Append a message to the short-term memory."""

        message: MemoryMessage = {
            "role": role,  # type: ignore[assignment]
            "content": content,
            "timestamp": datetime.utcnow(),
        }

        async with self._lock:
            queue = self._messages.setdefault(key, deque())
            queue.append(message)
            self._prune(queue)
            self._counts[key] = self._counts.get(key, 0) + 1

    async def reset(self, key: str) -> None:
        """Remove all memory associated with a key."""

        async with self._lock:
            self._messages.pop(key, None)
            self._counts.pop(key, None)

    def _prune(self, queue: Deque[MemoryMessage]) -> None:
        """Remove expired entries and enforce max history length."""

        ttl = self._config.ttl
        max_messages = max(2, self._config.max_messages)

        if ttl is not None:
            cutoff = datetime.utcnow() - ttl
            while queue and queue[0]["timestamp"] < cutoff:
                queue.popleft()

        while len(queue) > max_messages:
            queue.popleft()

    def get_total_count(self, key: str) -> int:
        """Return the total number of messages observed for a key."""

        return self._counts.get(key, 0)


class ConversationSummaryStore:
    """Thread-safe in-memory store for conversation summaries."""

    def __init__(self) -> None:
        self._summaries: Dict[str, SummaryEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> SummaryEntry:
        async with self._lock:
            entry = self._summaries.get(key)
            if entry is None:
                return SummaryEntry()
            return SummaryEntry(
                summary=entry.summary,
                message_count=entry.message_count,
                updated_at=entry.updated_at,
            )

    async def save(self, key: str, summary: str, message_count: int) -> None:
        async with self._lock:
            self._summaries[key] = SummaryEntry(
                summary=summary,
                message_count=message_count,
                updated_at=datetime.utcnow(),
            )

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._summaries.pop(key, None)
