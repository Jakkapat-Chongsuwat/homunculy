"""Agent Response Models - HTTP response schemas for agent operations."""

from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class AudioFormat(str, Enum):
    """Supported audio formats for TTS."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class AudioEncoding(str, Enum):
    """Supported audio encodings for transport."""
    BASE64 = "base64"
    URL = "url"


class AudioResponse(BaseModel):
    """Strongly-typed audio response - always present in response."""
    data: str = Field(default="", description="Audio data (base64-encoded or URL). Empty string if audio not generated.")
    format: AudioFormat = Field(default=AudioFormat.MP3, description="Audio file format")
    encoding: AudioEncoding = Field(default=AudioEncoding.BASE64, description="How audio is encoded for transport")
    size_bytes: int = Field(default=0, description="Original audio size in bytes (0 if not generated)")
    voice_id: str = Field(default="", description="Voice ID used for synthesis (empty if not generated)")
    duration_ms: Optional[int] = Field(default=None, description="Audio duration in milliseconds")
    generated: bool = Field(default=False, description="Whether audio was actually generated")


class AgentExecutionMetadata(BaseModel):
    """Metadata about agent execution."""
    model_used: Optional[str] = Field(default=None, description="Actual LLM model used for response")
    tokens_used: Optional[int] = Field(default=None, description="Total tokens consumed")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    tools_called: list[str] = Field(default_factory=list, description="List of tools invoked during execution")
    checkpointer_state: Optional[str] = Field(default=None, description="Conversation state checkpoint ID")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread ID")
    storage_type: Optional[str] = Field(default=None, description="Checkpointer storage type (postgres/memory)")


class ChatResponse(BaseModel):
    """HTTP response model for chat execution with audio."""
    model_config = ConfigDict(from_attributes=True)
    
    message: str = Field(description="Agent's response message")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    reasoning: str = Field(default="", description="Agent's reasoning process (if available)")
    audio: AudioResponse = Field(default_factory=AudioResponse, description="TTS audio structure (always present, check 'generated' field)")
    metadata: AgentExecutionMetadata = Field(default_factory=AgentExecutionMetadata, description="Execution metadata")
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request tracking ID")
