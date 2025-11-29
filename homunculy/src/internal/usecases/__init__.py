"""
Use Cases (Application Layer).

This package contains application-specific business logic that orchestrates
the domain entities and repository operations. Use cases are the entry points
for application operations.

Structure:
- agent/: Agent CRUD and chat operations
- streaming/: Real-time streaming operations (LLM + TTS)
"""

from internal.usecases.agent import (
    # Protocols
    ChatWithAgentUseCase,
    CreateAgentUseCase,
    DeleteAgentUseCase,
    GetAgentUseCase,
    ListAgentsUseCase,
    UpdateAgentUseCase,
    # Implementations
    ChatWithAgentUseCaseImpl,
    CreateAgentUseCaseImpl,
    DeleteAgentUseCaseImpl,
    GetAgentUseCaseImpl,
    ListAgentsUseCaseImpl,
    UpdateAgentUseCaseImpl,
)
from internal.usecases.streaming import (
    # Protocols
    StreamChatUseCase,
    TTSStreamingUseCase,
    # Implementations
    StreamChatUseCaseImpl,
    TTSStreamingUseCaseImpl,
    # Utilities
    SentenceBuffer,
    create_sentence_buffer,
)

__all__ = [
    # Agent Protocols
    "CreateAgentUseCase",
    "GetAgentUseCase",
    "ListAgentsUseCase",
    "UpdateAgentUseCase",
    "DeleteAgentUseCase",
    "ChatWithAgentUseCase",
    # Agent Implementations
    "CreateAgentUseCaseImpl",
    "GetAgentUseCaseImpl",
    "ListAgentsUseCaseImpl",
    "UpdateAgentUseCaseImpl",
    "DeleteAgentUseCaseImpl",
    "ChatWithAgentUseCaseImpl",
    # Streaming Protocols
    "StreamChatUseCase",
    "TTSStreamingUseCase",
    # Streaming Implementations
    "StreamChatUseCaseImpl",
    "TTSStreamingUseCaseImpl",
    # Utilities
    "SentenceBuffer",
    "create_sentence_buffer",
]
