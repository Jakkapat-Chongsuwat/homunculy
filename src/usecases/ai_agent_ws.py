"""
WebSocket-specific use cases for AI agent chat.

This module provides a thin application-layer function that
creates a Unit of Work per incoming WebSocket message, calls
the agent repository to perform the chat operation, and returns
the domain response. Keeping this logic in the use case layer
keeps adapters (controllers) thin and improves testability.
"""
from typing import Any, Dict, Optional, AsyncIterator

from di.dependency_injection import injector
from di.unit_of_work import AbstractAIAgentUnitOfWork
from models.ai_agent.ai_agent import AgentResponse


async def process_ws_message(
    agent_id: str,
    message: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> AgentResponse:
    """Process a single WebSocket chat message.

    - Obtains a fresh AbstractAIAgentUnitOfWork from the injector
      (so each message has a fresh transactional scope).
    - Calls the ai_agent_repo.chat(...) repository method and
      returns the AgentResponse.

    This function intentionally keeps the scope small and focused
    so controllers don't manage repository or UoW details.
    """
    uow: AbstractAIAgentUnitOfWork = injector.get(AbstractAIAgentUnitOfWork)
    context = context or {}

    async with uow:
        response = await uow.ai_agent_repo.chat(
            agent_id=agent_id,
            message=message,
            thread_id=thread_id,
            context=context,
        )

    return response


async def process_ws_stream(
  agent_id: str,
  message: str,
  thread_id: Optional[str] = None,
  context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[AgentResponse]:
  uow: AbstractAIAgentUnitOfWork = injector.get(AbstractAIAgentUnitOfWork)
  context = context or {}

  async with uow:
    async for resp in uow.ai_agent_repo.chat_stream(
      agent_id=agent_id,
      message=message,
      thread_id=thread_id,
      context=context,
    ):
      yield resp
