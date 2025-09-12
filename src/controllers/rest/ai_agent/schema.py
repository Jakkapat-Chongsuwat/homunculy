"""
AI Agent REST API Schemas.

This module defines Pydantic models for AI agent REST API requests and responses,
following the schema pattern established in the Pokemon system.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from common.type import UUIDStr


class AgentPersonalityRequest(BaseModel):
    """Request model for agent personality."""

    name: str = Field(..., description="Agent's name")
    description: str = Field(..., description="Agent description")
    traits: Dict[str, float] = Field(
        default_factory=dict,
        description="Personality traits as key-value pairs (0.0-1.0)"
    )
    mood: str = Field(default="neutral", description="Current mood state")
    memory_context: str = Field(default="", description="Long-term memory context")


class CreateAgentRequest(BaseModel):
    """Request model for creating an AI agent."""

    provider: str = Field(..., description="AI provider (pydantic_ai, openai, langraph, autogen)")
    model_name: str = Field(..., description="Model name for the provider")
    personality: AgentPersonalityRequest
    system_prompt: str = Field(default="", description="System-level instructions")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for response generation")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens in response")
    tools: List[str] = Field(default_factory=list, description="Available tools/functions")


class UpdateAgentRequest(BaseModel):
    """Request model for updating an AI agent."""

    personality: Optional[AgentPersonalityRequest] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    tools: Optional[List[str]] = None


class ChatRequest(BaseModel):
    """Request model for chatting with an agent."""

    message: str = Field(..., description="Message to send to the agent")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread ID")
    context: Optional[Dict] = Field(default=None, description="Additional context")


class AgentPersonalityResponse(BaseModel):
    """Response model for agent personality."""

    name: str = Field(..., description="Agent's name")
    description: str = Field(..., description="Agent description")
    traits: Dict[str, float] = Field(..., description="Personality traits")
    mood: str = Field(..., description="Current mood state")
    memory_context: str = Field(..., description="Long-term memory context")


class AgentConfigurationResponse(BaseModel):
    """Response model for agent configuration."""

    provider: str = Field(..., description="AI provider")
    model_name: str = Field(..., description="Model name")
    personality: AgentPersonalityResponse
    system_prompt: str = Field(..., description="System prompt")
    temperature: float = Field(..., description="Temperature setting")
    max_tokens: int = Field(..., description="Maximum tokens")
    tools: List[str] = Field(..., description="Available tools")


class AgentMessageResponse(BaseModel):
    """Response model for agent messages."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")


class AgentResponse(BaseModel):
    """Response model for agent responses."""

    message: str = Field(..., description="Agent's response message")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    reasoning: Optional[str] = Field(default=None, description="Agent's reasoning")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")
    status: str = Field(..., description="Response status")


class AgentThreadResponse(BaseModel):
    """Response model for agent threads."""

    id: str = Field(..., description="Thread ID")
    agent_id: str = Field(..., description="Agent ID")
    messages: List[AgentMessageResponse] = Field(default_factory=list, description="Thread messages")
    created_at: datetime = Field(..., description="Thread creation timestamp")
    updated_at: datetime = Field(..., description="Thread last update timestamp")
    metadata: Dict = Field(default_factory=dict, description="Thread metadata")


class AgentProviderResponse(BaseModel):
    """Response model for agent providers."""

    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    models: List[str] = Field(default_factory=list, description="Available models")


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""

    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Current status")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    thread_count: int = Field(default=0, description="Number of active threads")
    message_count: int = Field(default=0, description="Total message count")


class CreateAgentResponse(BaseModel):
    """Response model for agent creation."""

    agent_id: str = Field(..., description="Created agent ID")
    status: str = Field(default="created", description="Creation status")


class GenericResponse(BaseModel):
    """Generic response model for simple operations."""

    status: str = Field(..., description="Operation status")
    message: Optional[str] = Field(default=None, description="Optional message")