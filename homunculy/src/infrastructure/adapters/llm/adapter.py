"""LangGraph LLM adapter implementing LLMPort."""

from collections.abc import AsyncIterator
from typing import Any

from common.logger import get_logger
from domain.entities import AgentConfiguration, AgentResponse
from domain.interfaces import LLMPort
from infrastructure.adapters.llm.graph_manager import GraphManager
from infrastructure.adapters.llm.helpers import (
    build_messages,
    extract_response,
    invoke_graph,
    is_first_message,
    runnable_config,
    stream_graph,
)

logger = get_logger(__name__)


class LangGraphLLMAdapter(LLMPort):
    """LangGraph-based LLM adapter implementing LLMPort."""

    def __init__(
        self,
        graph_manager: GraphManager,
    ) -> None:
        self._graph_manager = graph_manager
        logger.info("LangGraph LLM adapter initialized")

    async def chat(
        self,
        config: AgentConfiguration,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Send chat message and return response."""
        thread_id = _resolve_thread_id(context)
        graph = await self._get_graph(config)
        result = await self._invoke(graph, config, message, thread_id)
        return _build_response(result, thread_id)

    async def _get_graph(self, config: AgentConfiguration) -> Any:
        """Get or build graph for configuration."""
        return await self._graph_manager.get_or_build(config)

    async def _invoke(
        self,
        graph: Any,
        config: AgentConfiguration,
        message: str,
        thread_id: str,
    ) -> dict:
        """Invoke graph with message."""
        run_config = runnable_config(thread_id)
        is_first = await is_first_message(graph, run_config, thread_id)
        messages = build_messages(config, message, is_first)
        return await invoke_graph(graph, messages, run_config)

    def stream_chat(
        self,
        config: AgentConfiguration,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat response chunks."""
        thread_id = _resolve_thread_id(context)
        return self._stream_impl(config, message, thread_id)

    async def _stream_impl(
        self,
        config: AgentConfiguration,
        message: str,
        thread_id: str,
    ) -> AsyncIterator[str]:
        """Internal streaming implementation."""
        graph = await self._get_graph(config)
        async for chunk in stream_graph(graph, config, message, thread_id):
            yield chunk


def _resolve_thread_id(context: dict[str, Any] | None) -> str:
    """Extract thread ID from context."""
    if not context:
        return "default"
    return context.get("thread_id", "default")


def _build_response(result: dict, thread_id: str) -> AgentResponse:
    """Build AgentResponse from graph result."""
    message = extract_response(result)
    return AgentResponse(
        message=message,
        confidence=1.0,
        metadata={"thread_id": thread_id},
    )
