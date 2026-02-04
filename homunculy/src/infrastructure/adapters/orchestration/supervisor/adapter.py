"""
LangGraph Supervisor Adapter.

Uses the official langgraph-supervisor-py library for multi-agent orchestration.
Supervisor automatically routes to specialized agents via tool-based handoffs.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from pydantic import SecretStr

from common.logger import get_logger
from domain.interfaces.orchestration import (
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
    SupervisorPort,
)

logger = get_logger(__name__)


class LangGraphSupervisorAdapter(SupervisorPort):
    """Official LangGraph Supervisor implementation.

    Uses langgraph-supervisor-py for automatic agent routing.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model_name = model
        self._model = ChatOpenAI(api_key=SecretStr(api_key), model=model)
        self._agents: dict[str, Any] = {}
        self._compiled_supervisor: Any = None

    async def close(self) -> None:
        """Close HTTP connections gracefully."""
        # ChatOpenAI uses httpx under the hood via OpenAI client
        # Access the underlying httpx client properly
        try:
            if hasattr(self._model, "async_client") and self._model.async_client:
                http_client = getattr(self._model.async_client, "_client", None)
                if http_client and hasattr(http_client, "aclose"):
                    await http_client.aclose()
        except Exception:
            pass  # Best effort cleanup

    async def route(self, input_: OrchestrationInput) -> str:
        """Route is handled automatically by supervisor."""
        # With langgraph-supervisor, routing is automatic
        # This method exists for interface compatibility
        return "supervisor"

    async def delegate(self, agent_name: str, input_: OrchestrationInput) -> OrchestrationOutput:
        """Delegate to supervisor - it handles routing."""
        supervisor = self._get_or_build_supervisor()
        result = await supervisor.ainvoke(
            {"messages": [{"role": "user", "content": input_.message}]},
            {"configurable": {"thread_id": input_.session_id}},
        )
        return _to_output(result)

    def register_agent(self, name: str, agent: OrchestratorPort) -> None:
        """Register a LangGraph agent (not OrchestratorPort for now)."""
        # For langgraph-supervisor, we need actual LangGraph agents
        # This stores them for supervisor compilation
        self._agents[name] = agent
        self._compiled_supervisor = None  # Reset to recompile
        logger.info("Agent registered", name=name)

    def register_react_agent(
        self,
        name: str,
        tools: list,
        prompt: str,
    ) -> None:
        """Register a ReAct agent with tools."""
        agent = create_react_agent(
            model=self._model,
            tools=tools,
            name=name,
            prompt=prompt,
        )
        self._agents[name] = agent
        self._compiled_supervisor = None
        logger.info("ReAct agent registered", name=name, tools=len(tools))

    def get_compiled_graph(self) -> Any:
        """Get the compiled LangGraph supervisor (for LiveKit integration)."""
        return self._get_or_build_supervisor()

    def _get_or_build_supervisor(self) -> Any:
        """Get or build the compiled supervisor."""
        if self._compiled_supervisor:
            return self._compiled_supervisor
        if not self._agents:
            raise ValueError("No agents registered with supervisor")
        workflow = create_supervisor(
            agents=list(self._agents.values()),
            model=self._model,
            prompt=_supervisor_prompt(list(self._agents.keys())),
        )
        self._compiled_supervisor = workflow.compile()
        logger.info("Supervisor compiled", agents=list(self._agents.keys()))
        return self._compiled_supervisor


class SupervisorOrchestrator(OrchestratorPort):
    """Wraps LangGraphSupervisorAdapter as OrchestratorPort."""

    def __init__(self, supervisor: LangGraphSupervisorAdapter) -> None:
        self._supervisor = supervisor

    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        """Invoke supervisor."""
        return await self._supervisor.delegate("supervisor", input_)

    async def stream(self, input_: OrchestrationInput) -> AsyncIterator[str]:
        """Stream not yet implemented for supervisor."""
        result = await self.invoke(input_)
        yield result.message

    async def close(self) -> None:
        """Close supervisor connections."""
        await self._supervisor.close()


# --- Helpers ---


def _supervisor_prompt(agent_names: list[str]) -> str:
    """Build supervisor system prompt."""
    agents_desc = _agents_description(agent_names)
    return f"""You are Homunculy, a team supervisor managing specialized agents.

Available agents:
{agents_desc}

Route user requests to the appropriate agent based on their expertise.
For general conversation, use the companion agent.
For technical questions, use the appropriate specialist.

Be helpful, friendly, and coordinate effectively between agents."""


def _agents_description(names: list[str]) -> str:
    """Generate agent descriptions."""
    descriptions = {
        "companion": "- companion: Friendly conversational AI for general chat",
        "math_expert": "- math_expert: Handles calculations and math problems",
        "researcher": "- researcher: Searches for information and facts",
        "coder": "- coder: Helps with programming and code questions",
    }
    lines = [descriptions.get(n, f"- {n}: Specialized agent") for n in names]
    return "\n".join(lines)


def _to_output(result: dict) -> OrchestrationOutput:
    """Convert LangGraph result to output."""
    messages = result.get("messages", [])
    if not messages:
        return OrchestrationOutput(message="")
    # Debug log all messages
    for i, msg in enumerate(messages):
        logger.debug(
            "Supervisor message",
            index=i,
            role=_message_role(msg),
            name=_message_name(msg),
            content=_message_content(msg)[:100] if _message_content(msg) else "",
        )
    content = _select_visible_content(messages)
    logger.debug("Selected content", content=content[:100] if content else "")
    return OrchestrationOutput(message=content)


def _select_visible_content(messages: list[Any]) -> str:
    """Pick the most user-visible assistant content.

    Skips:
    - Tool messages
    - Supervisor handoff messages
    - Empty messages
    """
    for msg in reversed(messages):
        content = _message_content(msg)
        if not content:
            continue
        if not _is_user_visible(msg):
            continue
        # Skip handoff messages from supervisor
        if _is_handoff_message(content):
            continue
        return content
    # Fallback: find ANY assistant content that's not a handoff
    for msg in reversed(messages):
        content = _message_content(msg)
        if content and not _is_handoff_message(content):
            return content
    return _message_content(messages[-1])


def _is_handoff_message(content: str) -> bool:
    """Check if this is a supervisor handoff message."""
    lower = content.lower()
    handoff_phrases = [
        "transferring to",
        "transferring back",
        "handing off to",
        "routing to",
        "delegating to",
        "transfer_to_",
    ]
    return any(phrase in lower for phrase in handoff_phrases)


def _message_content(msg: Any) -> str:
    """Get content from a message-like object."""
    if hasattr(msg, "content"):
        return msg.content or ""
    if isinstance(msg, dict):
        return msg.get("content") or ""
    return str(msg)


def _message_role(msg: Any) -> str:
    """Get role/type from a message-like object."""
    if hasattr(msg, "type"):
        return str(msg.type)
    if isinstance(msg, dict):
        return str(msg.get("role") or "")
    return ""


def _message_name(msg: Any) -> str:
    """Get name from a message-like object."""
    if hasattr(msg, "name"):
        return str(msg.name)
    if isinstance(msg, dict):
        return str(msg.get("name") or "")
    return ""


def _is_user_visible(msg: Any) -> bool:
    """True if this message should be shown to the user."""
    role = _message_role(msg)
    name = _message_name(msg)
    if role in {"tool", "function"}:
        return False
    if name == "supervisor":
        return False
    return role in {"assistant", "ai", ""}
