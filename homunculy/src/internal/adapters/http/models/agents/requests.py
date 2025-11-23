"""Agent Request Models - HTTP request schemas for agent operations."""

from pydantic import BaseModel, Field


class AgentPersonalityRequest(BaseModel):
    """Request model for agent personality configuration."""
    name: str = Field(description="Agent name/identity")
    description: str = Field(description="Brief description of agent's purpose")
    traits: dict = Field(default_factory=dict, description="Personality traits (e.g., {'humor': 'witty', 'tone': 'professional'})")
    mood: str = Field(default="neutral", description="Current mood state (e.g., neutral, excited, serious)")


class AgentConfigurationRequest(BaseModel):
    """Request model for complete agent configuration."""
    provider: str = Field(default="langraph", description="AI orchestration provider (currently only 'langraph')")
    model_name: str = Field(default="gpt-4", description="LLM model to use (e.g., gpt-4, gpt-3.5-turbo)")
    personality: AgentPersonalityRequest = Field(description="Agent personality configuration")
    system_prompt: str = Field(default="", description="System prompt override (optional)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response randomness (0.0=deterministic, 2.0=creative)")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens in response")


class ExecuteChatRequest(BaseModel):
    """
    Request model for stateless agent execution.
    
    Homunculy is a stateless execution engine - Management Service sends
    complete agent configuration with each request. No config is stored.
    """
    user_id: str = Field(description="User ID for conversation isolation and checkpointing")
    message: str = Field(description="User message to send to agent")
    configuration: AgentConfigurationRequest = Field(description="Complete agent configuration (not stored)")
    context: dict = Field(default_factory=dict, description="Additional conversation context (session_id, metadata, etc.)")
    include_audio: bool = Field(default=True, description="Generate and include TTS audio in response (default: enabled if TTS available)")
