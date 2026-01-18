"""
Supervisor Agent - Orchestrates specialist agents.

The Supervisor routes requests to the appropriate specialist agent.
Uses SupervisorPort for actual orchestration (LangGraph/AutoGen).

Clean Architecture:
- Pure domain logic
- Uses domain interfaces (SupervisorPort, AgentPort)
- No framework dependencies (LangGraph/LiveKit in infrastructure)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.interfaces import AgentInput, AgentOutput, AgentPort

if TYPE_CHECKING:
    from domain.interfaces import SupervisorPort


@dataclass(frozen=True)
class SessionContext:
    """Immutable session context."""

    session_id: str
    user_id: str
    room: str = ""
    personality: str = "default"
    metadata: dict | None = None


class SupervisorAgent(AgentPort):
    """Supervisor that routes to specialist agents.

    Framework-agnostic - uses SupervisorPort for orchestration.
    Can be backed by LangGraph supervisor, AutoGen swarm, etc.
    """

    def __init__(self, ctx: SessionContext, supervisor: "SupervisorPort") -> None:
        self._ctx = ctx
        self._supervisor = supervisor

    @property
    def name(self) -> str:
        """Agent name."""
        return "supervisor"

    @property
    def greeting_prompt(self) -> str:
        """Prompt for initial greeting."""
        return _greeting_prompt()

    async def process(self, input_: AgentInput) -> AgentOutput:
        """Route input to appropriate specialist."""
        from domain.interfaces import OrchestrationInput

        orch_input = OrchestrationInput(
            message=input_.text,
            session_id=input_.context.session_id,
            context={"personality": self._ctx.personality},
        )
        result = await self._supervisor.delegate("supervisor", orch_input)
        return AgentOutput(text=result.message)

    async def stream(self, input_: AgentInput) -> AsyncIterator[str]:
        """Stream response - supervisor delegates to specialists."""
        result = await self.process(input_)
        yield result.text


def create_supervisor(ctx: SessionContext, supervisor: "SupervisorPort") -> SupervisorAgent:
    """Factory for creating supervisor agent."""
    return SupervisorAgent(ctx, supervisor)


def _greeting_prompt() -> str:
    """Generate greeting prompt."""
    return "Greet the user briefly and ask how you can help."
