"""
Agent Use Cases Package.

This package provides use case implementations for agent operations,
following Clean Architecture's single responsibility principle.
"""

from internal.usecases.agent.chat_with_agent import ChatWithAgentUseCaseImpl
from internal.usecases.agent.create_agent import CreateAgentUseCaseImpl
from internal.usecases.agent.delete_agent import DeleteAgentUseCaseImpl
from internal.usecases.agent.get_agent import GetAgentUseCaseImpl
from internal.usecases.agent.interfaces import (
    ChatWithAgentUseCase,
    CreateAgentUseCase,
    DeleteAgentUseCase,
    GetAgentUseCase,
    ListAgentsUseCase,
    UpdateAgentUseCase,
)
from internal.usecases.agent.list_agents import ListAgentsUseCaseImpl
from internal.usecases.agent.update_agent import UpdateAgentUseCaseImpl

__all__ = [
    # Protocols
    "CreateAgentUseCase",
    "GetAgentUseCase",
    "ListAgentsUseCase",
    "UpdateAgentUseCase",
    "DeleteAgentUseCase",
    "ChatWithAgentUseCase",
    # Implementations
    "CreateAgentUseCaseImpl",
    "GetAgentUseCaseImpl",
    "ListAgentsUseCaseImpl",
    "UpdateAgentUseCaseImpl",
    "DeleteAgentUseCaseImpl",
    "ChatWithAgentUseCaseImpl",
]
