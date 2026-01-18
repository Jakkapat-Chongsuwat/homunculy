"""
Agent Router - Routes to specialist agents via LangGraph.

Uses LangGraph StateGraph to:
1. Analyze user intent
2. Route to appropriate specialist
3. Handle handoffs between agents
"""

from __future__ import annotations

from domain.interfaces import AgentInput, AgentPort, AgentRouterPort


class LangGraphRouter(AgentRouterPort):
    """Routes to specialists using LangGraph."""

    def __init__(self, llm: AgentPort, specialists: dict[str, AgentPort]) -> None:
        self._llm = llm
        self._specialists = specialists

    async def route(self, input_: AgentInput) -> str:
        """Determine which agent handles the input."""
        intent = await self._classify(input_.text)
        return _map_intent(intent)

    def get_agent(self, name: str) -> AgentPort:
        """Get specialist by name."""
        return self._specialists.get(name, self._llm)

    async def _classify(self, text: str) -> str:
        """Classify user intent."""
        prompt = _classification_prompt(text)
        output = await self._llm.process(_wrap_prompt(prompt))
        return _extract_intent(output.text)


def _classification_prompt(text: str) -> str:
    """Build intent classification prompt."""
    return f"""Classify the intent:
Text: {text}

Categories: general, sales, support, technical
Return only the category name."""


def _wrap_prompt(prompt: str) -> AgentInput:
    """Wrap prompt in AgentInput."""
    from domain.interfaces.agent import AgentContext

    ctx = AgentContext(session_id="router", user_id="system", room="", metadata={})
    return AgentInput(text=prompt, context=ctx)


def _extract_intent(text: str) -> str:
    """Extract intent from LLM response."""
    text = text.strip().lower()
    if "sales" in text:
        return "sales"
    if "support" in text or "technical" in text:
        return "support"
    return "general"


def _map_intent(intent: str) -> str:
    """Map intent to agent name."""
    mapping = {"sales": "sales", "support": "tech_support", "general": "supervisor"}
    return mapping.get(intent, "supervisor")
