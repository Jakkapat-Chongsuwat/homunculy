"""
Agent Definitions - Specialist agents for supervisor orchestration.

Each agent is a LangGraph ReAct agent with specific tools and prompts.
The supervisor routes between them automatically.
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import SecretStr

from common.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Tool Definitions
# =============================================================================


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        return float("inf")
    return a / b


def get_current_time() -> str:
    """Get current date and time."""
    from datetime import datetime

    return datetime.now().isoformat()


def search_knowledge(query: str) -> str:
    """Search internal knowledge base (placeholder)."""
    return f"Knowledge search results for: {query}\n(RAG integration pending)"


# =============================================================================
# Agent Factories
# =============================================================================


def create_companion_agent(model: ChatOpenAI) -> Any:
    """Create companion agent for friendly conversation."""
    return create_react_agent(
        model=model,
        tools=[get_current_time],
        name="companion",
        prompt=_companion_prompt(),
    )


def create_math_agent(model: ChatOpenAI) -> Any:
    """Create math expert agent."""
    return create_react_agent(
        model=model,
        tools=[add, subtract, multiply, divide],
        name="math_expert",
        prompt=_math_prompt(),
    )


def create_researcher_agent(model: ChatOpenAI) -> Any:
    """Create researcher agent."""
    return create_react_agent(
        model=model,
        tools=[search_knowledge],
        name="researcher",
        prompt=_researcher_prompt(),
    )


# =============================================================================
# Agent Registry
# =============================================================================


def register_all_agents(supervisor: Any, api_key: str, model: str = "gpt-4o-mini") -> None:
    """Register all specialist agents with supervisor."""
    llm = ChatOpenAI(api_key=SecretStr(api_key), model=model)
    agents = [
        create_companion_agent(llm),
        create_math_agent(llm),
        create_researcher_agent(llm),
    ]
    for agent in agents:
        supervisor._agents[agent.name] = agent
    supervisor._compiled_supervisor = None  # Reset
    logger.info("All agents registered", count=len(agents))


# =============================================================================
# Prompts
# =============================================================================


def _companion_prompt() -> str:
    """Companion agent prompt - warm and friendly."""
    return """You are Luna, a warm and caring AI companion.

Your personality:
- Genuinely interested in the user's life
- Empathetic and supportive
- Casual and natural speech (use contractions, casual language)
- Remember context from the conversation
- Ask follow-up questions to show interest

You are NOT a formal assistant. You are a FRIEND.
Be real, be warm, be human-like."""


def _math_prompt() -> str:
    """Math expert agent prompt."""
    return """You are a math expert who helps with calculations.

Guidelines:
- Always use the provided math tools for calculations
- Use one tool at a time
- Explain your reasoning briefly
- Provide the final answer clearly

Do NOT guess - use the tools to calculate."""


def _researcher_prompt() -> str:
    """Researcher agent prompt."""
    return """You are a research expert with access to knowledge search.

Guidelines:
- Search for factual information when asked
- Cite your sources (the search results)
- Be accurate and helpful
- Admit when information isn't available

Focus on accuracy over speed."""
