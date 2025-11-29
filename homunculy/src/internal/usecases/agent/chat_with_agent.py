"""
Chat With Agent Use Case.

Single Responsibility: Handle chat interactions with an agent.
"""

from typing import Optional

from internal.domain.entities import AgentResponse
from internal.domain.repositories import AgentRepository
from internal.domain.services import LLMService


class ChatWithAgentUseCaseImpl:
    """Use case for chatting with an agent."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        llm_service: LLMService,
    ) -> None:
        """
        Initialize the use case.

        Args:
            agent_repository: Repository for agent operations
            llm_service: LLM service for AI interactions
        """
        self._repository = agent_repository
        self._llm_service = llm_service

    async def execute(
        self,
        agent_id: str,
        message: str,
        context: Optional[dict] = None,
    ) -> AgentResponse:
        """
        Send a message to an agent and get response.

        Args:
            agent_id: Unique identifier for the agent
            message: User message
            context: Optional context dictionary

        Returns:
            Agent response
        """
        agent = await self._repository.get_by_id(agent_id)
        if not agent:
            return AgentResponse(
                message=f"Agent {agent_id} not found",
                confidence=0.0,
                reasoning="Agent does not exist",
            )

        try:
            return await self._llm_service.chat(
                configuration=agent.configuration,
                message=message,
                context=context,
            )
        except Exception as e:
            return AgentResponse(
                message=f"Error: {str(e)}",
                confidence=0.0,
                reasoning="Failed to communicate with LLM",
            )
