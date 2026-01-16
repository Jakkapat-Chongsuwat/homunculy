"""Agent repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from internal.domain.entities import Agent, AgentConfiguration


class AgentRepository(ABC):
    """Agent persistence contract."""

    @abstractmethod
    async def create(self, agent: Agent) -> Agent:
        """Create a new agent."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by id."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        """Update an agent."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """Delete an agent by id."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        """List agents with pagination."""
        raise NotImplementedError

    @abstractmethod
    async def update_configuration(self, agent_id: str, configuration: AgentConfiguration) -> bool:
        """Update agent configuration."""
        raise NotImplementedError
