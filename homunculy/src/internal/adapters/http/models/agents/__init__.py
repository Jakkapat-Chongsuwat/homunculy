"""Agent HTTP Models - Agent-specific request/response structures."""

from .requests import (
    AgentConfigurationRequest,
    AgentPersonalityRequest,
    ExecuteChatRequest,
)
from .responses import (
    AgentExecutionMetadata,
    AudioEncoding,
    AudioFormat,
    AudioResponse,
    ChatResponse,
)

__all__ = [
    # Requests
    "AgentPersonalityRequest",
    "AgentConfigurationRequest",
    "ExecuteChatRequest",
    # Responses
    "AudioFormat",
    "AudioEncoding",
    "AudioResponse",
    "ChatResponse",
    "AgentExecutionMetadata",
]
