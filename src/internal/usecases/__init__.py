"""
Use Cases (Application Layer).

This package contains application-specific business logic that orchestrates
the domain entities and repository operations. Use cases are the entry points
for application operations.
"""

from .interfaces import (
    CreateAgentUseCase,
    GetAgentUseCase,
    ListAgentsUseCase,
    UpdateAgentUseCase,
    DeleteAgentUseCase,
    ChatWithAgentUseCase,
)
from .agent_usecases import (
    CreateAgentUseCaseImpl,
    GetAgentUseCaseImpl,
    ListAgentsUseCaseImpl,
    UpdateAgentUseCaseImpl,
    DeleteAgentUseCaseImpl,
    ChatWithAgentUseCaseImpl,
)

__all__ = [
    # Protocols (structural interfaces)
    "CreateAgentUseCase",
    "GetAgentUseCase",
    "ListAgentsUseCase",
    "UpdateAgentUseCase",
    "DeleteAgentUseCase",
    "ChatWithAgentUseCase",
    # Concrete implementations
    "CreateAgentUseCaseImpl",
    "GetAgentUseCaseImpl",
    "ListAgentsUseCaseImpl",
    "UpdateAgentUseCaseImpl",
    "DeleteAgentUseCaseImpl",
    "ChatWithAgentUseCaseImpl",
]
