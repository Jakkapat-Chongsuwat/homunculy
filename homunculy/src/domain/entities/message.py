"""Message domain entity."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(Enum):
    """Message role types."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Message(BaseModel):
    """Conversation message."""

    id: str
    role: MessageRole
    content: str
    thread_id: str
    created_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_user(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER

    def is_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT
