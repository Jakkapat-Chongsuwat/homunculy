"""HTTP Request/Response Models.

Organized by module:
- common: Base response structures (ErrorResponse, SuccessResponse, etc.)
- agents: Agent-specific models (requests and responses)
"""

# Common base models
# Agent models
from .agents import (
    AgentConfigurationRequest,
    AgentExecutionMetadata,
    AgentPersonalityRequest,
    AudioEncoding,
    AudioFormat,
    AudioResponse,
    ChatResponse,
    ExecuteChatRequest,
)
from .common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    SuccessResponse,
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
