"""Agent domain entities and value objects."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentProvider(Enum):
    """Supported agent providers."""

    OPENAI = "openai"
    LANGRAPH = "langraph"


class AgentStatus(Enum):
    """Agent execution status."""

    IDLE = "idle"
    THINKING = "thinking"
    RESPONDING = "responding"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentMessage:
    """Message in a conversation."""

    role: str
    content: str
    timestamp: datetime
    metadata: dict[str, Any] | None = None


class AgentResponse(BaseModel):
    """Agent response output."""

    message: str
    confidence: float
    reasoning: str | None = None
    metadata: dict[str, Any] | None = None
    status: AgentStatus = AgentStatus.COMPLETED


class AgentPersonality(BaseModel):
    """Agent personality traits."""

    name: str = Field(..., description="Agent's name")
    description: str = Field(..., description="Agent description")
    traits: dict[str, float] = Field(default_factory=dict)
    mood: str = Field(default="neutral")
    memory_context: str = Field(default="")


class AgentConfiguration(BaseModel):
    """Agent configuration."""

    provider: AgentProvider
    model_name: str
    personality: AgentPersonality
    system_prompt: str = Field(default="")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    tools: list[str] = Field(default_factory=list)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AgentThread(BaseModel):
    """Conversation thread."""

    id: str
    agent_id: str
    messages: list[AgentMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Agent(BaseModel):
    """Agent entity with configuration and state."""

    id: str
    name: str
    configuration: AgentConfiguration
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def activate(self) -> None:
        """Activate the agent."""
        self.is_active = True
        self.updated_at = _now()

    def deactivate(self) -> None:
        """Deactivate the agent."""
        self.is_active = False
        self.updated_at = _now()
