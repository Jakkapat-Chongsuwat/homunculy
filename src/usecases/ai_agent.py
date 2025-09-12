"""
AI Agent Use Cases.

This module implements the business logic use cases for AI agents,
following the use case pattern established in the Pokemon system.
Use cases work directly with repositories through Unit of Work.
"""

from typing import AsyncIterator, Dict, List, Optional

from di.unit_of_work import AbstractAIAgentUnitOfWork
from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
)


async def initialize_ai_agent(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork, config: AgentConfiguration
) -> str:
    """Initialize an AI agent and store its configuration."""
    async with ai_agent_unit_of_work as aauow:
        agent_id = await aauow.ai_agent_repo.initialize_agent(config)
        return agent_id


async def chat_with_agent(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    agent_id: str,
    message: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict] = None,
) -> AgentResponse:
    """Send a message to an AI agent and get response."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.chat(agent_id, message, thread_id, context)


async def stream_chat_with_agent(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    agent_id: str,
    message: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict] = None,
) -> AsyncIterator[AgentResponse]:
    """Send a message to an AI agent and get streaming response."""
    async with ai_agent_unit_of_work as aauow:
        async for response in aauow.ai_agent_repo.chat_stream(agent_id, message, thread_id, context):
            yield response


async def update_agent_personality(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    agent_id: str,
    personality: AgentPersonality,
) -> bool:
    """Update an agent's personality."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.update_agent_personality(agent_id, personality)


async def get_agent_configuration(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    agent_id: str
) -> Optional[AgentConfiguration]:
    """Get agent configuration."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.get_agent_config(agent_id)


async def get_agent_status(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    agent_id: str
) -> Dict:
    """Get current status of an agent."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.get_agent_status(agent_id)


async def get_conversation_history(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    thread_id: str
) -> List[AgentMessage]:
    """Get conversation history for a thread."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.get_thread_history(thread_id)


async def clear_conversation_history(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    thread_id: str
) -> bool:
    """Clear conversation history for a thread."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.clear_thread_history(thread_id)


async def shutdown_agent(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork,
    agent_id: str
) -> bool:
    """Shutdown an AI agent."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.shutdown_agent(agent_id)


async def list_available_providers(
    ai_agent_unit_of_work: AbstractAIAgentUnitOfWork
) -> List[AgentProvider]:
    """List all available AI agent providers."""
    async with ai_agent_unit_of_work as aauow:
        return await aauow.ai_agent_repo.list_available_providers()