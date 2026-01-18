"""
LangGraph Orchestration Adapter.

Implements OrchestrationPort using LangGraph.
Can be swapped for AutoGen adapter in the future.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from common.logger import get_logger
from domain.interfaces.orchestration import (
    CheckpointerPort,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
    SupervisorPort,
)

logger = get_logger(__name__)


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


class LangGraphSupervisor(SupervisorPort):
    """LangGraph supervisor managing multiple agents."""

    def __init__(self, model: Any) -> None:
        self._model = model
        self._agents: dict[str, OrchestratorPort] = {}

    async def route(self, input_: OrchestrationInput) -> str:
        """Determine which agent handles input."""
        # Simple intent classification
        prompt = _route_prompt(input_.message, list(self._agents.keys()))
        result = await self._model.ainvoke(prompt)
        return _parse_route(result.content, self._agents.keys())

    async def delegate(self, agent_name: str, input_: OrchestrationInput) -> OrchestrationOutput:
        """Delegate to named agent."""
        agent = self._agents.get(agent_name)
        if not agent:
            return OrchestrationOutput(message=f"Unknown agent: {agent_name}")
        return await agent.invoke(input_)

    def register_agent(self, name: str, agent: OrchestratorPort) -> None:
        """Register agent with supervisor."""
        self._agents[name] = agent
        logger.info("Agent registered", name=name)


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


def _route_prompt(message: str, agents: list[str]) -> str:
    """Build routing prompt."""
    agent_list = ", ".join(agents) if agents else "companion"
    return f"""Classify which agent should handle: "{message}"
Available: {agent_list}
Reply with just the agent name."""


def _parse_route(response: str, agents: Any) -> str:
    """Parse routing response."""
    clean = response.strip().lower()
    for agent in agents:
        if agent.lower() in clean:
            return agent
    return "companion"  # Default
