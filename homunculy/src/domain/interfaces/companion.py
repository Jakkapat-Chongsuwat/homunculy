"""Companion Port - Core AI companion interface.

This is the main port for the "Yui/Jarvis" style companion.
It abstracts the full companion experience including:
- Personality-aware responses
- Memory integration
- Tool orchestration
- Emotional context
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EmotionalTone(Enum):
    """Emotional tone for companion responses."""

    NEUTRAL = "neutral"
    CHEERFUL = "cheerful"
    CONCERNED = "concerned"
    EXCITED = "excited"
    THOUGHTFUL = "thoughtful"
    SUPPORTIVE = "supportive"


@dataclass(frozen=True)
class CompanionContext:
    """Context for companion interaction."""

    session_id: str
    user_id: str
    channel: str = "default"
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompanionInput:
    """Input to companion."""

    message: str
    context: CompanionContext
    include_memory: bool = True
    include_persona: bool = True


@dataclass
class CompanionOutput:
    """Output from companion."""

    message: str
    tone: EmotionalTone = EmotionalTone.NEUTRAL
    tool_results: list[dict[str, Any]] | None = None
    memories_used: list[str] | None = None
    metadata: dict[str, Any] | None = None


class CompanionPort(ABC):
    """Core companion contract - main AI interaction."""

    @abstractmethod
    async def chat(self, input_: CompanionInput) -> CompanionOutput:
        """Process chat and return response."""
        ...

    @abstractmethod
    def stream(self, input_: CompanionInput) -> AsyncIterator[str]:
        """Stream response chunks."""
        ...

    @abstractmethod
    async def get_greeting(self, context: CompanionContext) -> str:
        """Get personalized greeting based on context."""
        ...

    async def close(self) -> None:
        """Close resources. Override if needed."""
        pass
