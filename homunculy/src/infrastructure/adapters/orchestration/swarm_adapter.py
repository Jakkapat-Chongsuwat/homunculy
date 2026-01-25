"""LangGraph Swarm orchestrator (handoff pattern)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from pydantic import SecretStr

from domain.interfaces.orchestration import (
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
)


class SwarmOrchestrator(OrchestratorPort):
    """Swarm-based orchestrator with agent handoffs."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._app = _build_swarm(api_key, model)

    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        """Invoke swarm and return final response."""
        result = await _invoke(self._app, input_)
        return _to_output(result)

    async def stream(self, input_: OrchestrationInput) -> AsyncIterator[str]:
        """Stream response chunks (fallback to full response)."""
        output = await self.invoke(input_)
        yield output.message


def _build_swarm(api_key: str, model: str) -> Any:
    """Build swarm with assistant and coder agents."""
    model_client = ChatOpenAI(api_key=SecretStr(api_key), model=model)
    assistant = _assistant_agent(model_client)
    coder = _coder_agent(model_client)
    builder = create_swarm([assistant, coder], default_active_agent="assistant")
    return builder.compile(checkpointer=MemorySaver())


def _assistant_agent(model: ChatOpenAI) -> Any:
    """Create assistant agent."""
    return create_react_agent(
        model=model,
        tools=[
            create_handoff_tool(agent_name="coder", description="Transfer to coder for programming")
        ],
        name="assistant",
        prompt=_assistant_prompt(),
    )


def _coder_agent(model: ChatOpenAI) -> Any:
    """Create coder agent."""
    return create_react_agent(
        model=model,
        tools=[
            create_handoff_tool(agent_name="assistant", description="Transfer back to assistant")
        ],
        name="coder",
        prompt=_coder_prompt(),
    )


def _assistant_prompt() -> str:
    return """You are a friendly assistant.

When the user asks about coding, transfer to the coder agent."""


def _coder_prompt() -> str:
    return """You are a coding specialist.

When the task is complete, transfer back to the assistant."""


async def _invoke(app: Any, input_: OrchestrationInput) -> dict:
    payload = {"messages": [{"role": "user", "content": input_.message}]}
    config = {"configurable": {"thread_id": input_.session_id}}
    return await app.ainvoke(payload, config)


def _to_output(result: dict) -> OrchestrationOutput:
    messages = result.get("messages", [])
    if not messages:
        return OrchestrationOutput(message="")
    last = messages[-1]
    content = last.content if hasattr(last, "content") else str(last)
    return OrchestrationOutput(message=content)
