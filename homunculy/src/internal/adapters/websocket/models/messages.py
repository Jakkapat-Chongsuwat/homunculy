"""WebSocket Message Models - Real-time streaming message schemas."""

from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from settings.tts import tts_settings


class MessageType(str, Enum):
    """WebSocket message types for protocol handling."""
    
    # Client -> Server
    CHAT_REQUEST = "chat_request"
    PING = "ping"
    
    # Server -> Client
    TEXT_CHUNK = "text_chunk"
    AUDIO_CHUNK = "audio_chunk"
    METADATA = "metadata"
    COMPLETE = "complete"
    ERROR = "error"
    PONG = "pong"
    CONNECTION_STATUS = "connection_status"


class AgentPersonalityWS(BaseModel):
    """Agent personality configuration for WebSocket."""
    
    name: str = Field(description="Agent name/identity")
    description: str = Field(description="Brief description of agent's purpose")
    traits: dict = Field(default_factory=dict, description="Personality traits")
    mood: str = Field(default="neutral", description="Current mood state")


class AgentConfigurationWS(BaseModel):
    """Agent configuration for WebSocket streaming."""
    
    provider: str = Field(default="langraph", description="AI orchestration provider")
    model_name: str = Field(default="gpt-4", description="LLM model to use")
    personality: AgentPersonalityWS = Field(description="Agent personality configuration")
    system_prompt: str = Field(default="", description="System prompt override")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response randomness")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens in response")


class ChatStreamRequest(BaseModel):
    """Client request to initiate streaming chat."""
    
    model_config = ConfigDict(from_attributes=True)
    
    type: MessageType = Field(default=MessageType.CHAT_REQUEST, description="Message type")
    user_id: str = Field(description="User ID for conversation isolation")
    message: str = Field(description="User message to send to agent")
    configuration: AgentConfigurationWS = Field(description="Complete agent configuration")
    context: dict = Field(default_factory=dict, description="Additional conversation context")
    stream_audio: bool = Field(default=True, description="Stream TTS audio chunks")
    voice_id: str = Field(
        default_factory=lambda: tts_settings.default_voice_id,
        description="ElevenLabs voice ID"
    )


class ChatStreamResponse(BaseModel):
    """Server response with text chunk."""
    
    model_config = ConfigDict(from_attributes=True)
    
    type: MessageType = Field(default=MessageType.TEXT_CHUNK, description="Message type")
    chunk: str = Field(description="Text chunk from AI response")
    chunk_index: int = Field(description="Sequential chunk number (0-indexed)")
    is_final: bool = Field(default=False, description="Whether this is the final text chunk")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Chunk timestamp (UTC)"
    )


class AudioChunk(BaseModel):
    """Server response with audio chunk."""
    
    model_config = ConfigDict(from_attributes=True)
    
    type: MessageType = Field(default=MessageType.AUDIO_CHUNK, description="Message type")
    data: str = Field(description="Base64-encoded audio chunk (MP3)")
    chunk_index: int = Field(description="Sequential chunk number (0-indexed)")
    is_final: bool = Field(default=False, description="Whether this is the final audio chunk")
    size_bytes: int = Field(description="Original chunk size in bytes")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Chunk timestamp (UTC)"
    )


class StreamMetadata(BaseModel):
    """Metadata about the streaming session."""
    
    type: MessageType = Field(default=MessageType.METADATA, description="Message type")
    model_used: Optional[str] = Field(default=None, description="LLM model used")
    tokens_used: Optional[int] = Field(default=None, description="Total tokens consumed")
    execution_time_ms: Optional[float] = Field(default=None, description="Total execution time")
    tools_called: list[str] = Field(default_factory=list, description="Tools invoked")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread ID")
    voice_id: Optional[str] = Field(default=None, description="Voice ID used for TTS")
    total_text_chunks: int = Field(default=0, description="Total text chunks sent")
    total_audio_chunks: int = Field(default=0, description="Total audio chunks sent")


class CompleteMessage(BaseModel):
    """Stream completion notification."""
    
    type: MessageType = Field(default=MessageType.COMPLETE, description="Message type")
    message: str = Field(default="Stream completed successfully", description="Completion message")
    metadata: StreamMetadata = Field(description="Session metadata")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Completion timestamp (UTC)"
    )


class ErrorMessage(BaseModel):
    """Error notification."""
    
    type: MessageType = Field(default=MessageType.ERROR, description="Message type")
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict = Field(default_factory=dict, description="Additional error context")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Error timestamp (UTC)"
    )


class ConnectionStatus(BaseModel):
    """Connection status notification."""
    
    type: MessageType = Field(default=MessageType.CONNECTION_STATUS, description="Message type")
    status: str = Field(description="Connection status (connected, ready, disconnected)")
    message: str = Field(default="", description="Status message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Status timestamp (UTC)"
    )
