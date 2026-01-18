"""
LiveKit Agent Adapters - Bridge domain agents to LiveKit framework.

This module adapts pure domain agents to LiveKit's Agent class.
When switching to another framework, create new adapters here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from livekit.agents import Agent

from common.logger import get_logger

if TYPE_CHECKING:
    from agents.companion import CompanionContext
    from agents.supervisor import SessionContext
    from domain.interfaces import OrchestratorPort, SupervisorPort

logger = get_logger(__name__)


class LiveKitCompanionAdapter(Agent):
    """LiveKit adapter for CompanionAgent."""

    def __init__(
        self,
        ctx: "CompanionContext",
        orchestrator: "OrchestratorPort",
    ) -> None:
        from agents.companion import CompanionAgent

        self._agent = CompanionAgent(ctx, orchestrator)
        super().__init__(instructions=self._agent.system_prompt)

    async def on_enter(self) -> None:
        """Warm greeting on entry."""
        self.session.generate_reply(instructions=self._agent.greeting_prompt)


class LiveKitSupervisorAdapter(Agent):
    """LiveKit adapter for SupervisorAgent."""

    def __init__(
        self,
        ctx: "SessionContext",
        supervisor: "SupervisorPort",
    ) -> None:
        from agents.supervisor import SupervisorAgent

        self._agent = SupervisorAgent(ctx, supervisor)
        super().__init__(instructions=_supervisor_instructions(ctx))

    async def on_enter(self) -> None:
        """Greet user on room entry."""
        self.session.generate_reply(instructions=self._agent.greeting_prompt)


def create_livekit_companion(
    ctx: "CompanionContext",
    orchestrator: "OrchestratorPort",
) -> Agent:
    """Factory for LiveKit companion."""
    return LiveKitCompanionAdapter(ctx, orchestrator)


def create_livekit_supervisor(
    ctx: "SessionContext",
    supervisor: "SupervisorPort",
) -> Agent:
    """Factory for LiveKit supervisor."""
    return LiveKitSupervisorAdapter(ctx, supervisor)


def _supervisor_instructions(ctx: "SessionContext") -> str:
    """Build supervisor instructions for LiveKit."""
    return f"""You are Homunculy, an AI assistant.

Session: {ctx.session_id}
User: {ctx.user_id}
Personality: {ctx.personality}

Route requests to specialists or answer directly.
Be helpful, concise, and friendly."""
