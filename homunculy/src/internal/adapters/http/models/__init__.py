"""HTTP Request/Response Models.

Organized by module:
- common: Base response structures (ErrorResponse, SuccessResponse, etc.)
- agents: Agent-specific models (requests and responses)
"""

# Common base models
from .common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    PaginationMetadata,
    PaginatedResponse,
)

# Agent models
from .agents import (
    AgentPersonalityRequest,
    AgentConfigurationRequest,
    ExecuteChatRequest,
    ChatResponse,
    AgentExecutionMetadata,
    AudioResponse,
    AudioFormat,
    AudioEncoding,
)

__all__ = [
    # Common base models
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "PaginationMetadata",
    "PaginatedResponse",
    # Agent models
    "AgentPersonalityRequest",
    "AgentConfigurationRequest",
    "ExecuteChatRequest",
    "ChatResponse",
    "AgentExecutionMetadata",
    "AudioResponse",
    "AudioFormat",
    "AudioEncoding",
]
