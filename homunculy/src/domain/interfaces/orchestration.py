"""
Orchestration Ports - Abstract LangGraph/AutoGen.

These interfaces abstract the AI orchestration layer so you can
swap LangGraph for AutoGen (or any other framework) in the future.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OrchestrationConfig:
    """Configuration for orchestration."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OrchestrationInput:
    """Input to orchestration."""

    message: str
    session_id: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationOutput:
    """Output from orchestration."""

    message: str
    tool_calls: list[dict] | None = None
    metadata: dict[str, Any] | None = None


class OrchestratorPort(ABC):
    """Core orchestration contract - process messages."""

    @abstractmethod
    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        """Process input synchronously."""
        ...

    @abstractmethod
    def stream(self, input_: OrchestrationInput) -> AsyncIterator[str]:
        """Stream response chunks."""
        ...


class SupervisorPort(ABC):
    """Supervisor orchestrates multiple agents."""

    @abstractmethod
    async def route(self, input_: OrchestrationInput) -> str:
        """Determine which agent handles the input."""
        ...

    @abstractmethod
    async def delegate(self, agent_name: str, input_: OrchestrationInput) -> OrchestrationOutput:
        """Delegate work to a named agent."""
        ...

    @abstractmethod
    def register_agent(self, name: str, agent: OrchestratorPort) -> None:
        """Register an agent with the supervisor."""
        ...


class CheckpointerPort(ABC):
    """State persistence for conversations."""

    @abstractmethod
    async def save(self, session_id: str, state: dict[str, Any]) -> None:
        """Save session state."""
        ...

    @abstractmethod
    async def load(self, session_id: str) -> dict[str, Any] | None:
        """Load session state."""
        ...

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session state."""
        ...
