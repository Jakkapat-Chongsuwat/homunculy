"""
Configuration Mapper - Map WebSocket requests to domain entities.

Single Responsibility: Convert WebSocket DTOs to domain objects.
"""

from internal.adapters.websocket.models.messages import ChatStreamRequest
from internal.domain.entities import AgentProvider, AgentPersonality, AgentConfiguration


def map_personality(request: ChatStreamRequest) -> AgentPersonality:
    """Map request personality to domain entity."""
    return AgentPersonality(
        name=request.configuration.personality.name,
        description=request.configuration.personality.description,
        traits=request.configuration.personality.traits,
        mood=request.configuration.personality.mood,
    )


def map_provider(request: ChatStreamRequest) -> AgentProvider:
    """Map request provider to domain enum."""
    try:
        return AgentProvider(request.configuration.provider)
    except ValueError:
        return AgentProvider.LANGRAPH


def map_configuration(request: ChatStreamRequest) -> AgentConfiguration:
    """Map request to domain configuration."""
    return AgentConfiguration(
        provider=map_provider(request),
        model_name=request.configuration.model_name,
        personality=map_personality(request),
        system_prompt=request.configuration.system_prompt,
        temperature=request.configuration.temperature,
        max_tokens=request.configuration.max_tokens,
    )


def build_context(request: ChatStreamRequest) -> dict:
    """Build context dictionary from request."""
    context = request.context.copy()
    context["user_id"] = request.user_id
    context["include_audio"] = False
    return context
