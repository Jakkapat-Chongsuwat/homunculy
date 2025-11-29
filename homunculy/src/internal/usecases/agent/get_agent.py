"""
Get Agent Use Case.

Single Responsibility: Retrieve an agent by ID.
"""

from typing import Optional

from internal.domain.entities import Agent
from internal.domain.repositories import AgentRepository


class GetAgentUseCaseImpl:
    """Use case for retrieving an agent."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        """
        Initialize the use case.

        Args:
            agent_repository: Repository for agent persistence
        """
        self._repository = agent_repository

    async def execute(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            The agent entity if found, None otherwise
        """
        return await self._repository.get_by_id(agent_id)
