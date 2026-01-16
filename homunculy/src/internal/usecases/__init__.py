"""
Use Cases (Application Layer).

This package contains application-specific business logic that orchestrates
the domain entities and repository operations. Use cases are the entry points
for application operations.

Structure:
- agent/: Agent CRUD and chat operations
"""

from internal.usecases.agent import (
    # Protocols
    ChatWithAgentUseCase,
    # Implementations
    ChatWithAgentUseCaseImpl,
    CreateAgentUseCase,
    CreateAgentUseCaseImpl,
    DeleteAgentUseCase,
    DeleteAgentUseCaseImpl,
    GetAgentUseCase,
    GetAgentUseCaseImpl,
    ListAgentsUseCase,
    ListAgentsUseCaseImpl,
    UpdateAgentUseCase,
    UpdateAgentUseCaseImpl,
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
]
