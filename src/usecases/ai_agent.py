"""
AI Agent Use Cases.

This module implements the business logic use cases for AI agents,
following the use case pattern established in the Pokemon system.
Use cases work directly with repository layer (LLM providers).
"""

from typing import Dict, List, Optional

from repositories.llm_service.llm_factory import LLMFactory
from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentResponse,
)


async def create_llm_agent(
    llm_factory: LLMFactory,
    agent_id: str,
    config: AgentConfiguration
) -> None:
    """
    Create an LLM agent using the repository layer.
    
    This use case handles the business logic of creating LLM agents
    while delegating the actual LLM operations to the repository layer.
    """
    # Get the appropriate client from the factory
    provider_str = str(config.provider.value) if hasattr(config.provider, 'value') else str(config.provider)
    client = llm_factory.create_client(provider_str)
    
    # Create the agent using the repository
    await client.create_agent(config)
    
    # Note: In a full implementation, we might want to store agent metadata
    # in the repository, but for now we keep it simple


async def chat_with_llm_agent(
    llm_factory: LLMFactory,
    agent_id: str,
    message: str,
    context: Optional[Dict[str, str]] = None
) -> AgentResponse:
    """
    Send a message to an LLM agent and get response.
    
    This use case orchestrates the chat functionality using the repository layer.
    """
    # For now, we'll assume the agent was created with a known provider
    # In a full implementation, we'd look up the provider from the repository
    provider_str = "pydantic_ai"  # Default provider
    
    client = llm_factory.create_client(provider_str)
    return await client.chat(agent_id, message, context)


async def update_llm_agent(
    llm_factory: LLMFactory,
    agent_id: str,
    config: AgentConfiguration
) -> None:
    """
    Update an LLM agent's configuration.
    
    This use case handles updating agent configurations through the repository layer.
    """
    provider_str = str(config.provider.value) if hasattr(config.provider, 'value') else str(config.provider)
    client = llm_factory.create_client(provider_str)
    await client.update_agent(agent_id, config)


async def remove_llm_agent(
    llm_factory: LLMFactory,
    agent_id: str
) -> None:
    """
    Remove an LLM agent.
    
    This use case handles agent cleanup through the repository layer.
    """
    # For now, we'll try both providers (in a real implementation, 
    # we'd track which provider each agent uses)
    for provider in ["pydantic_ai", "openai"]:
        try:
            client = llm_factory.create_client(provider)
            await client.remove_agent(agent_id)
            break  # Success, no need to try other providers
        except Exception:
            continue  # Try next provider


def get_supported_llm_providers(
    llm_factory: LLMFactory
) -> List[str]:
    """
    Get list of supported LLM providers.
    
    This use case exposes the repository capabilities.
    """
    return llm_factory.get_supported_providers()