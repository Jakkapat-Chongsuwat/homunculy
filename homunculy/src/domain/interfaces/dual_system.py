"""
Dual-System Ports - Human-like cognitive architecture.

2026 Standard: Hybrid Dual-System Architecture
- ReflexPort: Fast responses (<300ms) - greetings, acknowledgments
- CognitionPort: Deep reasoning - complex tasks, tool use
- DualSystemPort: Orchestrates reflex + cognition in parallel

This mimics human cognition: "fast reflexes" + "slow reasoning".
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResponseType(str, Enum):
    """Type of response from dual-system."""

    REFLEX = "reflex"  # Fast, social, <300ms
    COGNITION = "cognition"  # Slow, deliberate


class EmotionalTone(str, Enum):
    """Detected emotional state."""

    NEUTRAL = "neutral"
    HAPPY = "happy"
    FRUSTRATED = "frustrated"
    URGENT = "urgent"
    CONFUSED = "confused"


@dataclass(frozen=True)
class DualSystemInput:
    """Input to dual-system processing."""

    text: str
    session_id: str
    audio_features: dict[str, float] | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflexOutput:
    """Fast response output (<300ms)."""

    text: str
    is_filler: bool = False  # "uh-huh", "I see", etc.
    confidence: float = 1.0


@dataclass
class CognitionOutput:
    """Deep reasoning output."""

    text: str
    tool_calls: list[dict] | None = None
    reasoning_trace: list[str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class DualSystemOutput:
    """Combined output from both systems."""

    response_type: ResponseType
    text: str
    reflex: ReflexOutput | None = None
    cognition: CognitionOutput | None = None
    emotion: EmotionalTone = EmotionalTone.NEUTRAL


class ReflexPort(ABC):
    """Fast response layer - <300ms target.

    Handles:
    - Greetings and social cues
    - Acknowledgments ("uh-huh", "I see")
    - Simple questions (time, weather)
    - Maintaining connection during cognition
    """

    @abstractmethod
    async def respond(self, input_: DualSystemInput) -> ReflexOutput:
        """Generate fast response."""
        ...

    @abstractmethod
    def can_handle(self, input_: DualSystemInput) -> bool:
        """Check if reflex can handle this input."""
        ...


class CognitionPort(ABC):
    """Deep reasoning layer - deliberate thinking.

    Handles:
    - Complex questions requiring research
    - Multi-step tasks with tool use
    - Code generation and debugging
    - Analysis and synthesis
    """

    @abstractmethod
    async def reason(self, input_: DualSystemInput) -> CognitionOutput:
        """Deep reasoning with full context."""
        ...

    @abstractmethod
    def stream(self, input_: DualSystemInput) -> AsyncIterator[str]:
        """Stream reasoning output."""
        ...


class EmotionDetectorPort(ABC):
    """Detect emotional state from input."""

    @abstractmethod
    async def detect(self, input_: DualSystemInput) -> EmotionalTone:
        """Detect emotion from text and audio features."""
        ...


class DualSystemPort(ABC):
    """Orchestrates reflex + cognition in parallel.

    This is the main entry point for human-like interaction.
    It decides whether to use fast reflex or deep cognition,
    and can run them in parallel (e.g., reflex says "let me think"
    while cognition processes).
    """

    @abstractmethod
    async def process(self, input_: DualSystemInput) -> DualSystemOutput:
        """Process with dual-system architecture."""
        ...

    @abstractmethod
    def stream(self, input_: DualSystemInput) -> AsyncIterator[DualSystemOutput]:
        """Stream responses - may include reflex then cognition."""
        ...

    @abstractmethod
    async def interrupt(self, session_id: str) -> None:
        """Interrupt ongoing cognition (user interrupted)."""
        ...
