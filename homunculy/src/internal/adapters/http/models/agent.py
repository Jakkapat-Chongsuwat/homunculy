"""Agent HTTP Request/Response Models."""

from pydantic import BaseModel, Field, ConfigDict


class AgentPersonalityRequest(BaseModel):
    """Request model for agent personality."""
    name: str
    description: str
    traits: dict = Field(default_factory=dict)
    mood: str = "neutral"


class AgentConfigurationRequest(BaseModel):
    """Request model for agent configuration."""
    provider: str = "langraph"
    model_name: str = "gpt-4"
    personality: AgentPersonalityRequest
    system_prompt: str = ""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)


class ExecuteChatRequest(BaseModel):
    """
    Request model for executing chat with full agent configuration (STATELESS).
    
    Used by Management Service to execute agent without storing config in Homunculy.
    Homunculy is a stateless execution engine - config is provided per request.
    """
    user_id: str = Field(description="User ID for conversation isolation")
    message: str = Field(description="User message to send to agent")
    configuration: AgentConfigurationRequest = Field(description="Complete agent configuration")
    context: dict = Field(default_factory=dict, description="Additional conversation context")


class ChatResponse(BaseModel):
    """HTTP response model for chat."""
    model_config = ConfigDict(from_attributes=True)
    
    message: str
    confidence: float
    reasoning: str = ""
    metadata: dict = Field(default_factory=dict, description="Additional response metadata")
