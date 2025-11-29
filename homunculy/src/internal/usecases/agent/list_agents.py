"""
List Agents Use Case.

Single Responsibility: List all agents with pagination.
"""

from typing import List

from internal.domain.entities import Agent
from internal.domain.repositories import AgentRepository


class ListAgentsUseCaseImpl:
    """Use case for listing agents."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        """
        Initialize the use case.

        Args:
            agent_repository: Repository for agent persistence
        """
        self._repository = agent_repository

    async def execute(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        """
        List all agents with pagination.

        Args:
            limit: Maximum number of agents to return
            offset: Number of agents to skip

        Returns:
            List of agent entities
        """
        return await self._repository.list_all(limit, offset)
