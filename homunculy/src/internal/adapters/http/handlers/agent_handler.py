"""
Agent Execution Handler (STATELESS).

This module provides the /execute endpoint for stateless agent execution.
Homunculy is a stateless execution engine - Management Service handles agent storage.

ARCHITECTURE:
- Homunculy = Stateless execution engine (this service)
- Management Service = Stores agent configs, orchestrates business logic
- This handler only provides chat execution capability
"""

from fastapi import APIRouter, Depends, HTTPException, status
from common.logger import get_logger
from internal.adapters.http.models import (
    ExecuteChatRequest,
    ChatResponse,
    AgentExecutionMetadata,
    AudioResponse,
)
from internal.domain.entities import AgentProvider, AgentPersonality, AgentConfiguration
from internal.domain.services import LLMService
from internal.infrastructure.container import get_llm_service


logger = get_logger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/execute", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def execute_chat(
    request: ExecuteChatRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> ChatResponse:
    """
    Execute chat with provided agent configuration (STATELESS).
    
    PRIMARY ENDPOINT for Management Service.
    - Agent configuration is passed in the request (not retrieved from database)
    - No agent storage in Homunculy
    - Conversation state stored in Postgres checkpointer by user_id/session
    
    Flow:
    1. Management Service sends: config + message + user_id
    2. Homunculy executes agent with LangGraph
    3. Returns chat response
    4. Homunculy remains stateless (no config stored)
    
    Args:
        request: Execution request with full agent config, message, user_id
        
    Returns:
        Chat response with message, confidence, metadata
    """
    try:
        # Map HTTP request to domain entities
        personality = AgentPersonality(
            name=request.configuration.personality.name,
            description=request.configuration.personality.description,
            traits=request.configuration.personality.traits,
            mood=request.configuration.personality.mood,
        )
        
        # Parse provider from request
        try:
            provider = AgentProvider(request.configuration.provider)
        except ValueError:
            provider = AgentProvider.LANGRAPH
        
        configuration = AgentConfiguration(
            provider=provider,
            model_name=request.configuration.model_name,
            personality=personality,
            system_prompt=request.configuration.system_prompt,
            temperature=request.configuration.temperature,
            max_tokens=request.configuration.max_tokens,
        )
        
        # LLM service injected via Depends() - proper Clean Architecture DI
        # Note: Service is injected by FastAPI, not called directly
        
        # Add user_id to context for conversation isolation
        context = request.context.copy()
        context["user_id"] = request.user_id
        context["include_audio"] = request.include_audio  # Pass audio flag to service
        
        # Execute chat (stateless - config not stored)
        response = await llm_service.chat(configuration, request.message, context)
        
        # Convert metadata dict to strongly-typed AgentExecutionMetadata
        metadata_dict = response.metadata or {}
        metadata = AgentExecutionMetadata(
            model_used=metadata_dict.get("model_used"),
            tokens_used=metadata_dict.get("tokens_used"),
            execution_time_ms=metadata_dict.get("execution_time_ms"),
            tools_called=metadata_dict.get("tools_called", []),
            checkpointer_state=metadata_dict.get("checkpointer_state"),
            thread_id=metadata_dict.get("thread_id"),
            storage_type=metadata_dict.get("storage_type"),
        )
        
        # Build strongly-typed AudioResponse (always present, might be empty)
        audio_data = metadata_dict.get("audio", {})
        audio = AudioResponse(
            data=audio_data.get("data", ""),
            format=audio_data.get("format", "mp3"),
            encoding=audio_data.get("encoding", "base64"),
            size_bytes=audio_data.get("size_bytes", 0),
            voice_id=audio_data.get("voice_id", ""),
            duration_ms=audio_data.get("duration_ms"),
            generated=bool(audio_data.get("data"))  # True if audio data exists
        )
        
        return ChatResponse(
            message=response.message,
            confidence=response.confidence,
            reasoning=response.reasoning or "",
            audio=audio,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error("Agent execution failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat execution failed: {str(e)}"
        )
