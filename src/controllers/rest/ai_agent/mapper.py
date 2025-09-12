"""
AI Agent REST API Mappers.

This module provides mappers to convert between REST API request/response models
and domain entities, following the mapper pattern established in the Pokemon system.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from common.docstring import MAPPER_DOCSTRING
from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
    AgentStatus,
    AgentThread,
)

from .schema import (
    AgentConfigurationResponse,
    AgentMessageResponse,
    AgentPersonalityRequest,
    AgentPersonalityResponse,
    AgentProviderResponse,
    AgentResponse as AgentResponseSchema,
    AgentStatusResponse,
    AgentThreadResponse,
    ChatRequest,
    CreateAgentRequest,
    UpdateAgentRequest,
)

__doc__ = MAPPER_DOCSTRING


class AgentRequestMapper:
    """Mapper for converting REST API requests to domain entities."""

    @staticmethod
    def create_request_to_entity(instance: CreateAgentRequest) -> AgentConfiguration:
        """Convert create agent request to domain entity."""
        return AgentConfiguration(
            provider=AgentProvider(instance.provider),
            model_name=instance.model_name,
            personality=AgentPersonality(
                name=instance.personality.name,
                description=instance.personality.description,
                traits=instance.personality.traits,
                mood=instance.personality.mood,
                memory_context=instance.personality.memory_context,
            ),
            system_prompt=instance.system_prompt,
            temperature=instance.temperature,
            max_tokens=instance.max_tokens,
            tools=instance.tools,
        )

    @staticmethod
    def update_request_to_entity(instance: UpdateAgentRequest) -> Dict:
        """Convert update agent request to dictionary for partial updates."""
        update_data = {}

        if instance.personality:
            update_data["personality"] = AgentPersonality(
                name=instance.personality.name,
                description=instance.personality.description,
                traits=instance.personality.traits,
                mood=instance.personality.mood,
                memory_context=instance.personality.memory_context,
            )

        if instance.system_prompt is not None:
            update_data["system_prompt"] = instance.system_prompt

        if instance.temperature is not None:
            update_data["temperature"] = instance.temperature

        if instance.max_tokens is not None:
            update_data["max_tokens"] = instance.max_tokens

        if instance.tools is not None:
            update_data["tools"] = instance.tools

        return update_data

    @staticmethod
    def chat_request_to_params(instance: ChatRequest) -> tuple[str, Optional[str], Optional[Dict]]:
        """Convert chat request to parameters."""
        return instance.message, instance.thread_id, instance.context


class AgentResponseMapper:
    """Mapper for converting domain entities to REST API responses."""

    @staticmethod
    def entity_to_response(instance: AgentResponse) -> AgentResponseSchema:
        """Convert domain response to API response."""
        return AgentResponseSchema(
            message=instance.message,
            confidence=instance.confidence,
            reasoning=instance.reasoning,
            metadata=instance.metadata,
            status=instance.status.value,
        )

    @staticmethod
    def configuration_to_response(instance: AgentConfiguration) -> AgentConfigurationResponse:
        """Convert agent configuration to API response."""
        return AgentConfigurationResponse(
            provider=instance.provider.value,
            model_name=instance.model_name,
            personality=AgentPersonalityResponse(
                name=instance.personality.name,
                description=instance.personality.description,
                traits=instance.personality.traits,
                mood=instance.personality.mood,
                memory_context=instance.personality.memory_context,
            ),
            system_prompt=instance.system_prompt,
            temperature=instance.temperature,
            max_tokens=instance.max_tokens,
            tools=instance.tools,
        )

    @staticmethod
    def personality_to_response(instance: AgentPersonality) -> AgentPersonalityResponse:
        """Convert agent personality to API response."""
        return AgentPersonalityResponse(
            name=instance.name,
            description=instance.description,
            traits=instance.traits,
            mood=instance.mood,
            memory_context=instance.memory_context,
        )

    @staticmethod
    def thread_to_response(instance: AgentThread) -> AgentThreadResponse:
        """Convert agent thread to API response."""
        return AgentThreadResponse(
            id=instance.id,
            agent_id=instance.agent_id,
            messages=[
                AgentMessageResponseMapper.entity_to_response(msg)
                for msg in instance.messages
            ],
            created_at=instance.created_at,
            updated_at=instance.updated_at,
            metadata=instance.metadata,
        )

    @staticmethod
    def providers_to_response(providers: List[AgentProvider]) -> List[AgentProviderResponse]:
        """Convert list of providers to API responses."""
        # Define available models for each provider
        provider_models = {
            AgentProvider.PYDANTIC_AI: ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-3.5-sonnet"],
            AgentProvider.OPENAI: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
            AgentProvider.LANGRAPH: ["gpt-4", "claude-3", "gemini-pro"],
            AgentProvider.AUTOGEN: ["gpt-4", "gpt-3.5-turbo", "claude-3"],
        }
        
        return [
            AgentProviderResponse(
                name=provider.value,
                display_name=provider.value.replace("_", " ").title(),
                models=provider_models.get(provider, []),
            )
            for provider in providers
        ]

    @staticmethod
    def status_to_response(
        agent_id: str,
        status: AgentStatus,
        thread_count: int = 0,
        message_count: int = 0,
        last_activity: Optional[datetime] = None,
    ) -> AgentStatusResponse:
        """Convert agent status to API response."""
        return AgentStatusResponse(
            agent_id=agent_id,
            status=status.value,
            last_activity=last_activity,
            thread_count=thread_count,
            message_count=message_count,
        )


class AgentMessageResponseMapper:
    """Mapper for agent messages."""

    @staticmethod
    def entity_to_response(instance: AgentMessage) -> AgentMessageResponse:
        """Convert domain message to API response."""
        return AgentMessageResponse(
            role=instance.role,
            content=instance.content,
            timestamp=instance.timestamp,
            metadata=instance.metadata,
        )