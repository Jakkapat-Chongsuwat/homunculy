"""
Create Agent Use Case.

Single Responsibility: Create a new agent.
"""

from internal.domain.entities import Agent, AgentConfiguration
from internal.domain.repositories import AgentRepository


class CreateAgentUseCaseImpl:
    """Use case for creating a new agent."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        """
        Initialize the use case.

        Args:
            agent_repository: Repository for agent persistence
        """
        self._repository = agent_repository

    async def execute(self, agent_id: str, name: str, configuration: AgentConfiguration) -> Agent:
        """
        Create a new agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Agent name
            configuration: Agent configuration

        Returns:
            The created agent entity
        """
        agent = Agent(
            id=agent_id,
            name=name,
            configuration=configuration,
        )
        return await self._repository.create(agent)
