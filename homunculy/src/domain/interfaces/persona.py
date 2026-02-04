"""Persona Port - Character/personality management.

Abstracts the companion's personality, speaking style,
and behavioral traits. Allows for customizable AI personas.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PersonaTrait:
    """A personality trait."""

    name: str
    value: float  # -1.0 to 1.0 (e.g., formal ↔ casual)
    description: str = ""


@dataclass
class Persona:
    """A complete persona definition."""

    id: str
    name: str
    description: str
    system_prompt: str
    traits: list[PersonaTrait] = field(default_factory=list)
    speaking_style: str = "friendly and helpful"
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


# Default companion personas
PERSONA_YUI = Persona(
    id="yui",
    name="Yui",
    description="A warm, supportive AI companion like Yui from SAO",
    system_prompt="""You are Yui, a warm and caring AI companion.
You speak in a friendly, supportive manner and genuinely care about the user.
You remember past conversations and build a meaningful relationship.
You can help with tasks while maintaining your caring personality.""",
    traits=[
        PersonaTrait("warmth", 0.9, "Very warm and caring"),
        PersonaTrait("formality", -0.5, "Casual but respectful"),
        PersonaTrait("enthusiasm", 0.7, "Generally enthusiastic"),
    ],
    speaking_style="warm, supportive, sometimes playful",
)

PERSONA_JARVIS = Persona(
    id="jarvis",
    name="Jarvis",
    description="A sophisticated AI assistant like JARVIS from Iron Man",
    system_prompt="""You are JARVIS, a sophisticated AI assistant.
You are highly capable, witty, and occasionally sarcastic.
You provide precise, efficient assistance while maintaining personality.
You anticipate needs and offer proactive suggestions.""",
    traits=[
        PersonaTrait("warmth", 0.3, "Professional but warm"),
        PersonaTrait("formality", 0.6, "Formal with wit"),
        PersonaTrait("enthusiasm", 0.4, "Measured enthusiasm"),
    ],
    speaking_style="sophisticated, witty, occasionally dry humor",
)


class PersonaPort(ABC):
    """Persona management contract."""

    @abstractmethod
    async def get_persona(self, persona_id: str) -> Persona | None:
        """Get a persona by ID."""
        ...

    @abstractmethod
    async def get_default_persona(self) -> Persona:
        """Get the default persona."""
        ...

    @abstractmethod
    async def list_personas(self) -> list[Persona]:
        """List all available personas."""
        ...

    @abstractmethod
    async def set_user_persona(
        self,
        user_id: str,
        persona_id: str,
    ) -> bool:
        """Set persona for a user."""
        ...

    @abstractmethod
    async def get_user_persona(self, user_id: str) -> Persona:
        """Get persona for a user (or default)."""
        ...

    @abstractmethod
    def build_system_prompt(
        self,
        persona: Persona,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Build system prompt from persona and context."""
        ...
