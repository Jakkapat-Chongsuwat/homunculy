"""
Agent Use Case Protocols.

Defines Protocol-based interfaces for agent-related use cases.
"""

from typing import List, Optional, Protocol

from internal.domain.entities import Agent, AgentConfiguration, AgentResponse


class CreateAgentUseCase(Protocol):
    """Protocol for creating an agent."""

    async def execute(self, agent_id: str, name: str, configuration: AgentConfiguration) -> Agent:
        """Create a new agent."""
        ...


class GetAgentUseCase(Protocol):
    """Protocol for retrieving an agent."""

    async def execute(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        ...


class ListAgentsUseCase(Protocol):
    """Protocol for listing agents."""

    async def execute(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        """List all agents with pagination."""
        ...


class UpdateAgentUseCase(Protocol):
    """Protocol for updating an agent."""

    async def execute(self, agent: Agent) -> Agent:
        """Update an existing agent."""
        ...


class DeleteAgentUseCase(Protocol):
    """Protocol for deleting an agent."""

    async def execute(self, agent_id: str) -> bool:
        """Delete an agent by ID."""
        ...


class ChatWithAgentUseCase(Protocol):
    """Protocol for chatting with an agent."""

    async def execute(
        self,
        agent_id: str,
        message: str,
        context: Optional[dict] = None,
    ) -> AgentResponse:
        """Send a message to an agent and get response."""
        ...
