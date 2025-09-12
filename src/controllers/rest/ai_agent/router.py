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
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    config = AgentRequestMapper.create_request_to_entity(body)
    agent_id = await ai_agent.initialize_ai_agent(ai_agent_unit_of_work, config)

    return CreateAgentResponse(agent_id=agent_id)


@router.post("/agents/{agent_id}/chat", response_model=AgentResponse)
async def chat_with_agent(
    agent_id: str,
    body: ChatRequest = Body(...),
) -> AgentResponse:
    """Send a message to an AI agent."""
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    message, thread_id, context = AgentRequestMapper.chat_request_to_params(body)
    response = await ai_agent.chat_with_agent(ai_agent_unit_of_work, agent_id, message, thread_id, context)

    return AgentResponseMapper.entity_to_response(response)


@router.put("/agents/{agent_id}/personality", response_model=GenericResponse)
async def update_agent_personality(
    agent_id: str = Path(..., description="Agent ID"),
    body: UpdateAgentRequest = Body(...),
) -> GenericResponse:
    """Update an agent's personality."""
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    update_data = AgentRequestMapper.update_request_to_entity(body)

    if "personality" in update_data:
        success = await ai_agent.update_agent_personality(
            ai_agent_unit_of_work, agent_id, update_data["personality"]
        )
        if not success:
            # Return error response instead of raising exception
            return GenericResponse(status="error", message=f"Agent not found: {agent_id}")

    return GenericResponse(status="updated")


@router.get("/agents/{agent_id}/config", response_model=AgentConfigurationResponse)
async def get_agent_config(
    agent_id: str = Path(..., description="Agent ID"),
) -> AgentConfigurationResponse:
    """Get agent configuration."""
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    config = await ai_agent.get_agent_configuration(ai_agent_unit_of_work, agent_id)

    if not config:
        # Return error response instead of raising exception
        return AgentConfigurationResponse(
            provider="",
            model_name="",
            personality=AgentPersonalityResponse(
                name="",
                description=f"Agent not found: {agent_id}",
                traits={},
                mood="",
                memory_context="",
            ),
            system_prompt="",
            temperature=0.0,
            max_tokens=0,
            tools=[],
        )

    return AgentResponseMapper.configuration_to_response(config)


@router.get("/agents/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str = Path(..., description="Agent ID"),
) -> AgentStatusResponse:
    """Get agent status."""
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    status_data = await ai_agent.get_agent_status(ai_agent_unit_of_work, agent_id)

    # Convert status dict to response model
    return AgentStatusResponse(
        agent_id=agent_id,
        status=status_data.get("status", "unknown"),
        last_activity=status_data.get("last_activity"),
        thread_count=status_data.get("thread_count", 0),
        message_count=status_data.get("message_count", 0),
    )


@router.get("/providers", response_model=List[AgentProviderResponse])
async def list_providers() -> List[AgentProviderResponse]:
    """List available AI providers."""
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    providers = await ai_agent.list_available_providers(ai_agent_unit_of_work)

    return AgentResponseMapper.providers_to_response(providers)


@router.delete("/agents/{agent_id}", response_model=GenericResponse)
async def shutdown_agent(
    agent_id: str = Path(..., description="Agent ID"),
) -> GenericResponse:
    """Shutdown an AI agent."""
    ai_agent_unit_of_work = injector.get(AbstractAIAgentUnitOfWork)
    success = await ai_agent.shutdown_agent(ai_agent_unit_of_work, agent_id)

    if not success:
        return GenericResponse(status="error", message=f"Agent not found: {agent_id}")

    return GenericResponse(status="shutdown")