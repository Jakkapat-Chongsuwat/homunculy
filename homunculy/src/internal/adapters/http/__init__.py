"""
HTTP Adapters (Controllers).

This package contains HTTP request handlers that adapt external HTTP requests
to use case calls. This is the interface adapter layer in Clean Architecture.
"""

from .handlers.agent_handler import router as agent_router
from .models import (
    ExecuteChatRequest,
    ChatResponse,
    AgentExecutionMetadata,
    AudioResponse,
)

__all__ = [
    "agent_router",
    "ExecuteChatRequest",
    "ChatResponse",
    "AgentExecutionMetadata",
    "AudioResponse",
]
