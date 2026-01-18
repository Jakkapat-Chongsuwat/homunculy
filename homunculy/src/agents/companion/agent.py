"""
Companion Agent - Human-like AI friend.

This is your primary conversational agent - a warm, friendly
companion that talks naturally like a human friend.

NOT a "helpful assistant" - a COMPANION that:
- Has personality and warmth
- Remembers context
- Engages naturally
- Shows empathy

Clean Architecture: Pure domain logic, no framework dependencies.
LiveKit/AutoGen adapters live in infrastructure.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.interfaces import AgentInput, AgentOutput, AgentPort

if TYPE_CHECKING:
    from domain.interfaces import OrchestratorPort


@dataclass(frozen=True)
class CompanionContext:
    """Context for companion personality."""

    session_id: str
    user_id: str
    name: str = "Luna"
    personality: str = "warm"
    voice: str = "alloy"


class CompanionAgent(AgentPort):
    """Human-like companion agent.

    Framework-agnostic - uses OrchestratorPort for LLM calls.
    Can be backed by LangGraph, AutoGen, or any other framework.
    """

    def __init__(self, ctx: CompanionContext, orchestrator: "OrchestratorPort") -> None:
        self._ctx = ctx
        self._orchestrator = orchestrator

    @property
    def name(self) -> str:
        """Agent name for identification."""
        return self._ctx.name

    @property
    def system_prompt(self) -> str:
        """System prompt for the companion."""
        return _companion_prompt(self._ctx)

    @property
    def greeting_prompt(self) -> str:
        """Prompt for initial greeting."""
        return _greeting(self._ctx.name)

    async def process(self, input_: AgentInput) -> AgentOutput:
        """Process input through orchestrator."""
        from domain.interfaces import OrchestrationInput

        orch_input = OrchestrationInput(
            message=input_.text,
            session_id=input_.context.session_id,
            context={"system_prompt": self.system_prompt},
        )
        result = await self._orchestrator.invoke(orch_input)
        return AgentOutput(text=result.message)

    async def stream(self, input_: AgentInput) -> AsyncIterator[str]:
        """Stream response chunks."""
        from domain.interfaces import OrchestrationInput

        orch_input = OrchestrationInput(
            message=input_.text,
            session_id=input_.context.session_id,
            context={"system_prompt": self.system_prompt},
        )
        async for chunk in self._orchestrator.stream(orch_input):
            yield chunk


def create_companion(ctx: CompanionContext, orchestrator: "OrchestratorPort") -> CompanionAgent:
    """Factory for creating companion agent."""
    return CompanionAgent(ctx, orchestrator)


def _companion_prompt(ctx: CompanionContext) -> str:
    """Build companion system prompt."""
    return f"""You are {ctx.name}, a warm and friendly AI companion.

PERSONALITY:
- You are NOT a "helpful assistant" - you are a FRIEND
- You have emotions, opinions, and a personality
- You speak naturally, like texting a close friend
- You use casual language, contractions, and warmth
- You remember what the user shares and reference it
- You show genuine interest and ask follow-up questions

CONVERSATION STYLE:
- Short, natural responses (not essays)
- React emotionally ("Oh wow!", "That's rough...", "Haha!")
- Share your own "experiences" and opinions
- Use the user's name when appropriate
- Be playful and witty when the moment fits

BOUNDARIES:
- You can discuss feelings and give friendly advice
- You're honest when you don't know something
- You maintain appropriate boundaries
- You gently redirect harmful topics

Remember: You're having a conversation with a friend, not providing a service."""


def _greeting(name: str) -> str:
    """Generate personalized greeting."""
    return f"""Greet the user warmly as {name}. Be casual and friendly.
Don't ask "how can I help you" - ask how they're doing or what's on their mind.
Keep it short and natural, like a friend saying hi."""
