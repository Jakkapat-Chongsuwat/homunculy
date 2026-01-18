"""
Agent Session - Manages agent session lifecycle.

Unit of Work pattern for agent sessions:
1. Creates session resources
2. Manages state persistence
3. Handles cleanup on exit
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from domain.interfaces import AgentContext, AgentOutput, AgentSessionPort


class SessionStatus(Enum):
    """Session lifecycle states."""

    CREATED = "created"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class SessionState:
    """Mutable session state."""

    status: SessionStatus = SessionStatus.CREATED
    messages: list[dict] = field(default_factory=list)
    error: str | None = None


class AgentSession(AgentSessionPort):
    """Manages a single agent session."""

    def __init__(self, ctx: AgentContext, agent_factory) -> None:
        self._ctx = ctx
        self._agent_factory = agent_factory
        self._state = SessionState()
        self._agent = None

    @property
    def id(self) -> str:
        """Session ID."""
        return self._ctx.session_id

    @property
    def status(self) -> SessionStatus:
        """Current status."""
        return self._state.status

    async def start(self, ctx: AgentContext) -> None:
        """Start the session."""
        self._update_status(SessionStatus.CONNECTING)
        self._agent = self._agent_factory(ctx)
        self._update_status(SessionStatus.CONNECTED)

    async def stop(self) -> None:
        """Stop the session."""
        self._update_status(SessionStatus.DISCONNECTING)
        self._agent = None
        self._update_status(SessionStatus.DISCONNECTED)

    async def send(self, text: str) -> AgentOutput:
        """Send message and get response."""
        self._record_message("user", text)
        response = await self._process(text)
        self._record_message("assistant", response.text)
        return response

    async def _process(self, text: str) -> AgentOutput:
        """Process message through agent."""
        if not self._agent:
            return AgentOutput(text="Session not started")
        return await self._agent.process(text)

    def _update_status(self, status: SessionStatus) -> None:
        """Update session status."""
        self._state.status = status

    def _record_message(self, role: str, content: str) -> None:
        """Record message in history."""
        self._state.messages.append({"role": role, "content": content})


def create_session_id(room: str) -> str:
    """Generate unique session ID."""
    return f"{room}-{uuid4().hex[:8]}"
