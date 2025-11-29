"""
Delete Agent Use Case.

Single Responsibility: Delete an agent by ID.
"""

from internal.domain.repositories import AgentRepository


class DeleteAgentUseCaseImpl:
    """Use case for deleting an agent."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        """
        Initialize the use case.

        Args:
            agent_repository: Repository for agent persistence
        """
        self._repository = agent_repository

    async def execute(self, agent_id: str) -> None:
        """
        Delete an agent.

        Args:
            agent_id: The ID of the agent to delete
        """
        await self._repository.delete(agent_id)
