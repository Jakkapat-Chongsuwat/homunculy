"""
Update Agent Use Case.

Single Responsibility: Update an existing agent.
"""

from internal.domain.entities import Agent
from internal.domain.repositories import AgentRepository


class UpdateAgentUseCaseImpl:
    """Use case for updating an agent."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        """
        Initialize the use case.

        Args:
            agent_repository: Repository for agent persistence
        """
        self._repository = agent_repository

    async def execute(self, agent: Agent) -> Agent:
        """
        Update an existing agent.

        Args:
            agent: The agent entity with updated data

        Returns:
            The updated agent entity
        """
        return await self._repository.update(agent)
