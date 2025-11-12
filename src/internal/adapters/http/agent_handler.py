"""
Agent HTTP Handler.

This module provides HTTP endpoints for agent operations using FastAPI.
It acts as an adapter layer, converting HTTP requests to use case calls.
Uses Dependency Injection for infrastructure and instantiates use cases per request.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from internal.usecases import (
    CreateAgentUseCase,
    CreateAgentUseCaseImpl,
    GetAgentUseCase,
    GetAgentUseCaseImpl,
    ListAgentsUseCase,
    ListAgentsUseCaseImpl,
    UpdateAgentUseCase,
    UpdateAgentUseCaseImpl,
    DeleteAgentUseCase,
    DeleteAgentUseCaseImpl,
    ChatWithAgentUseCase,
    ChatWithAgentUseCaseImpl,
)
from internal.domain.entities import AgentProvider, AgentPersonality, AgentConfiguration
from internal.domain.repositories import UnitOfWork
from internal.domain.services import LLMService
from internal.infrastructure.di import get_uow, get_llm_service


# Request/Response Models
class AgentPersonalityRequest(BaseModel):
    """Request model for agent personality."""
    name: str
    description: str
    traits: dict = Field(default_factory=dict)
    mood: str = "neutral"


class AgentConfigurationRequest(BaseModel):
    """Request model for agent configuration."""
    provider: str = "pydantic_ai"
    model_name: str = "gpt-4"
    personality: AgentPersonalityRequest
    system_prompt: str = ""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)


class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""
    name: str
    configuration: AgentConfigurationRequest


class CreateAgentResponse(BaseModel):
    """Response model for creating an agent."""
    id: str
    name: str
    status: str = "created"


class AgentResponse(BaseModel):
    """Response model for agent."""
    id: str
    name: str
    status: str
    is_active: bool
    created_at: str
    updated_at: str


class ChatRequest(BaseModel):
    """Request model for chatting with an agent."""
    message: str
    context: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for chat."""
    message: str
    confidence: float
    reasoning: str = ""


# Router setup
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/", response_model=CreateAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    uow: UnitOfWork = Depends(get_uow)
) -> CreateAgentResponse:
    """Create a new agent."""
    try:
        # Map request to domain entities
        personality = AgentPersonality(
            name=request.configuration.personality.name,
            description=request.configuration.personality.description,
            traits=request.configuration.personality.traits,
            mood=request.configuration.personality.mood,
        )
        
        # Parse provider from request string to enum
        try:
            provider = AgentProvider(request.configuration.provider)
        except ValueError:
            # Default to PydanticAI if invalid provider
            provider = AgentProvider.PYDANTIC_AI
        
        configuration = AgentConfiguration(
            provider=provider,
            model_name=request.configuration.model_name,
            personality=personality,
            system_prompt=request.configuration.system_prompt,
            temperature=request.configuration.temperature,
            max_tokens=request.configuration.max_tokens,
        )
        
        # Generate agent ID
        import uuid
        agent_id = str(uuid.uuid4())
        
        # Instantiate use case with repository from UoW
        use_case: CreateAgentUseCase = CreateAgentUseCaseImpl(uow.agents)
        agent = await use_case.execute(agent_id, request.name, configuration)
        
        # Commit transaction
        await uow.commit()
        
        return CreateAgentResponse(
            id=agent.id,
            name=agent.name,
            status="created"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    uow: UnitOfWork = Depends(get_uow)
) -> AgentResponse:
    """Get an agent by ID."""
    use_case: GetAgentUseCase = GetAgentUseCaseImpl(uow.agents)
    agent = await use_case.execute(agent_id)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        status=agent.status.value,
        is_active=agent.is_active,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    limit: int = 50,
    offset: int = 0,
    uow: UnitOfWork = Depends(get_uow)
) -> List[AgentResponse]:
    """List all agents."""
    use_case: ListAgentsUseCase = ListAgentsUseCaseImpl(uow.agents)
    agents = await use_case.execute(limit, offset)
    
    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            status=agent.status.value,
            is_active=agent.is_active,
            created_at=agent.created_at.isoformat(),
            updated_at=agent.updated_at.isoformat(),
        )
        for agent in agents
    ]


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    uow: UnitOfWork = Depends(get_uow)
):
    """Delete an agent."""
    use_case: DeleteAgentUseCase = DeleteAgentUseCaseImpl(uow.agents)
    deleted = await use_case.execute(agent_id)
    
    # Commit transaction
    await uow.commit()
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
    uow: UnitOfWork = Depends(get_uow)
) -> ChatResponse:
    """
    Chat with an agent.
    
    Dynamically selects the appropriate LLM service based on the agent's provider configuration.
    """
    # First, retrieve the agent to determine its provider
    agent = await uow.agents.get_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Get the appropriate LLM service for the agent's provider
    llm_service = get_llm_service(agent.configuration.provider)
    
    # Execute the chat use case
    use_case: ChatWithAgentUseCase = ChatWithAgentUseCaseImpl(uow.agents, llm_service)
    response = await use_case.execute(agent_id, request.message, request.context)
    
    return ChatResponse(
        message=response.message,
        confidence=response.confidence,
        reasoning=response.reasoning or "",
    )
