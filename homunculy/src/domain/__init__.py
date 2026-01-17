"""Domain layer - Core business entities and interfaces (framework-agnostic)."""

from domain.entities import (
    Agent,
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentResponse,
    AgentStatus,
    ConversationState,
    Message,
    MessageRole,
    Session,
)
from domain.interfaces import (
    LLMPort,
    RAGPort,
    STTPort,
    TTSPort,
)

__all__ = [
    # Entities
    "Agent",
    "AgentConfiguration",
    "AgentMessage",
    "AgentPersonality",
    "AgentResponse",
    "AgentStatus",
    "ConversationState",
    "Message",
    "MessageRole",
    "Session",
    # Interfaces (Ports)
    "LLMPort",
    "RAGPort",
    "STTPort",
    "TTSPort",
]
