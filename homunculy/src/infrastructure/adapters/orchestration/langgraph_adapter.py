"""
LangGraph Orchestration Adapter.

Implements OrchestrationPort using LangGraph.
Can be swapped for AutoGen adapter in the future.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from domain.interfaces.orchestration import (
    CheckpointerPort,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
)


class LangGraphOrchestrator(OrchestratorPort):
    """LangGraph implementation of OrchestratorPort."""

    def __init__(self, graph: Any, checkpointer: CheckpointerPort | None = None) -> None:
        self._graph = graph
        self._checkpointer = checkpointer

    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        """Invoke graph synchronously."""
        config = _run_config(input_.session_id)
        messages = _to_messages(input_.message)
        result = await self._graph.ainvoke({"messages": messages}, config)
        return _to_output(result)

    async def stream(self, input_: OrchestrationInput) -> AsyncIterator[str]:
        """Stream response chunks."""
        config = _run_config(input_.session_id)
        messages = _to_messages(input_.message)
        async for event in self._graph.astream_events({"messages": messages}, config):
            chunk = _extract_chunk(event)
            if chunk:
                yield chunk


# --- Helpers ---


def _run_config(session_id: str) -> dict:
    """Build LangGraph run config."""
    return {"configurable": {"thread_id": session_id}}


def _to_messages(text: str) -> list[dict]:
    """Convert text to message list."""
    return [{"role": "user", "content": text}]


def _to_output(result: dict) -> OrchestrationOutput:
    """Convert LangGraph result to output."""
    messages = result.get("messages", [])
    if not messages:
        return OrchestrationOutput(message="")
    last = messages[-1]
    content = last.content if hasattr(last, "content") else str(last)
    return OrchestrationOutput(message=content)


def _extract_chunk(event: dict) -> str | None:
    """Extract text chunk from stream event."""
    if event.get("event") != "on_chat_model_stream":
        return None
    data = event.get("data", {})
    chunk = data.get("chunk")
    return chunk.content if hasattr(chunk, "content") else None
