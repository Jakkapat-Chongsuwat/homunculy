"""
AI Agent REST API Routes.

This module provides REST API endpoints for AI agent operations,
following the Clean Architecture pattern established in the Pokemon system.
"""

from typing import List

from fastapi import APIRouter, Body, Path, status

from common.type import UUIDStr
from di.dependency_injection import injector
from di.unit_of_work import AbstractAIAgentUnitOfWork
from usecases import ai_agent
from models.ai_agent.ai_agent import AgentConfiguration, AgentProvider

from .mapper import AgentRequestMapper, AgentResponseMapper
from .schema import (
    AgentConfigurationResponse,
    AgentPersonalityResponse,
    AgentProviderResponse,
    AgentResponse,
    AgentStatusResponse,
    AgentThreadResponse,
    ChatRequest,
    CreateAgentRequest,
    CreateAgentResponse,
    GenericResponse,
    UpdateAgentRequest,
)

router = APIRouter()


@router.post("/agents", response_model=CreateAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(body: CreateAgentRequest) -> CreateAgentResponse:
    """Create a new AI agent."""
    from di.dependency_injection import injector
    from repositories.llm_service.llm_factory import LLMFactory

    llm_factory = injector.get(LLMFactory)
    config = AgentRequestMapper.create_request_to_entity(body)
    agent_id = await ai_agent.create_llm_agent(llm_factory, "", config)

    return CreateAgentResponse(agent_id=agent_id)


@router.post("/agents/{agent_id}/chat", response_model=AgentResponse)
async def chat_with_agent(
    agent_id: str,
    body: ChatRequest = Body(...),
) -> AgentResponse:
    """Send a message to an AI agent."""
    from di.dependency_injection import injector
    from repositories.llm_service.llm_factory import LLMFactory

    llm_factory = injector.get(LLMFactory)
    message, thread_id, context = AgentRequestMapper.chat_request_to_params(body)
    response = await ai_agent.chat_with_llm_agent(llm_factory, agent_id, message, context)

    return AgentResponseMapper.entity_to_response(response)


@router.put("/agents/{agent_id}/personality", response_model=GenericResponse)
async def update_agent_personality(
    agent_id: str = Path(..., description="Agent ID"),
    body: UpdateAgentRequest = Body(...),
) -> GenericResponse:
    """Update an agent's personality."""
    from di.dependency_injection import injector
    from repositories.llm_service.llm_factory import LLMFactory

    llm_factory = injector.get(LLMFactory)
    update_data = AgentRequestMapper.update_request_to_entity(body)

    if "personality" in update_data:
        config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,  # Default provider
            model_name="gpt-4",
            personality=update_data["personality"],
            system_prompt=update_data.get("system_prompt", ""),
            temperature=update_data.get("temperature", 0.7),
            max_tokens=update_data.get("max_tokens", 1000),
            tools=update_data.get("tools", []),
        )
        await ai_agent.update_llm_agent(llm_factory, agent_id, config)

    return GenericResponse(status="updated")


@router.get("/agents/{agent_id}/config", response_model=AgentConfigurationResponse)
async def get_agent_config(
    agent_id: str = Path(..., description="Agent ID"),
) -> AgentConfigurationResponse:
    """Get agent configuration."""
    # For now, return a default configuration
    # In a full implementation, this would retrieve the actual agent config
    return AgentConfigurationResponse(
        provider="pydantic_ai",
        model_name="gpt-4",
        personality=AgentPersonalityResponse(
            name="Default Agent",
            description="A helpful AI assistant",
            traits={"helpful": True, "creative": True},
            mood="neutral",
            memory_context="",
        ),
        system_prompt="You are a helpful AI assistant.",
        temperature=0.7,
        max_tokens=1000,
        tools=[],
    )


@router.get("/agents/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str = Path(..., description="Agent ID"),
) -> AgentStatusResponse:
    """Get agent status."""
    # For now, return a simple status response
    # In a full implementation, this would check the actual agent status
    from datetime import datetime
    return AgentStatusResponse(
        agent_id=agent_id,
        status="active",
        last_activity=datetime.now(),
        thread_count=1,
        message_count=0,
    )


@router.get("/providers", response_model=List[AgentProviderResponse])
async def list_providers() -> List[AgentProviderResponse]:
    """List available AI providers."""
    from di.dependency_injection import injector
    from repositories.llm_service.llm_factory import LLMFactory
    from models.ai_agent.ai_agent import AgentProvider

    llm_factory = injector.get(LLMFactory)
    provider_strings = ai_agent.get_supported_llm_providers(llm_factory)

    # Convert string list to AgentProvider enum list
    providers = [AgentProvider(provider_str) for provider_str in provider_strings]

    return AgentResponseMapper.providers_to_response(providers)


@router.delete("/agents/{agent_id}", response_model=GenericResponse)
async def shutdown_agent(
    agent_id: str = Path(..., description="Agent ID"),
) -> GenericResponse:
    """Shutdown an AI agent."""
    from di.dependency_injection import injector
    from repositories.llm_service.llm_factory import LLMFactory

    llm_factory = injector.get(LLMFactory)
    await ai_agent.remove_llm_agent(llm_factory, agent_id)

    return GenericResponse(status="shutdown")