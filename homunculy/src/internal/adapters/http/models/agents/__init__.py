"""Agent HTTP Models - Agent-specific request/response structures."""

from .requests import (
    AgentPersonalityRequest,
    AgentConfigurationRequest,
    ExecuteChatRequest,
)
from .responses import (
    AudioFormat,
    AudioEncoding,
    AudioResponse,
    AgentExecutionMetadata,
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
