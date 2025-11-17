"""Data models used by short-term memory components."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, Optional, TypedDict


class MemoryMessage(TypedDict):
    """Single conversational message stored in memory."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime


@dataclass(frozen=True)
class MemoryConfig:
    """Configuration for short-term memory retention."""

    max_messages: int = 8
    ttl: Optional[timedelta] = timedelta(minutes=15)


@dataclass
class SummaryEntry:
    """Represents the running summary for a conversation."""

    summary: str = ""
    message_count: int = 0
    updated_at: datetime = field(default_factory=datetime.utcnow)
