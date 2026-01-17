"""Session and conversation state entities."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConversationState(BaseModel):
    """State for LangGraph conversations."""

    messages: list[dict[str, Any]] = Field(default_factory=list)
    current_question: str = ""
    documents: list[dict[str, Any]] = Field(default_factory=list)
    generation: str = ""
    requires_tool_use: bool = False
    tool_results: list[dict[str, Any]] = Field(default_factory=list)


class Session(BaseModel):
    """User session for real-time communication."""

    id: str
    agent_id: str
    thread_id: str
    tenant_id: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.updated_at = _now()

    def close(self) -> None:
        """Close the session."""
        self.is_active = False
        self.updated_at = _now()
