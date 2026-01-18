"""
Agent Ports - Domain interfaces for agent system.

These are the contracts that the application layer uses.
Infrastructure adapters implement these interfaces.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentContext:
    """Immutable context passed to agents."""

    session_id: str
    user_id: str
    room: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AgentInput:
    """Input to agent processing."""

    text: str
    context: AgentContext


@dataclass
class AgentOutput:
    """Output from agent processing."""

    text: str
    audio: bytes | None = None
    metadata: dict[str, Any] | None = None


class AgentPort(ABC):
    """Core agent contract - process input, return output."""

    @abstractmethod
    async def process(self, input_: AgentInput) -> AgentOutput:
        """Process input and return output."""
        ...

    @abstractmethod
    def stream(self, input_: AgentInput) -> AsyncIterator[str]:
        """Stream response chunks."""
        ...


class AgentRouterPort(ABC):
    """Router that delegates to specialized agents."""

    @abstractmethod
    async def route(self, input_: AgentInput) -> str:
        """Determine which agent should handle input."""
        ...

    @abstractmethod
    def get_agent(self, name: str) -> AgentPort:
        """Get agent by name."""
        ...


class AgentSessionPort(ABC):
    """Manages agent session lifecycle."""

    @abstractmethod
    async def start(self, ctx: AgentContext) -> None:
        """Start agent session."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop agent session."""
        ...

    @abstractmethod
    async def send(self, text: str) -> AgentOutput:
        """Send message to agent."""
        ...
