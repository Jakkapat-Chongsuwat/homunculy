"""Route inbound channel messages through the orchestrator."""

from dataclasses import dataclass

from common.logger import get_logger
from domain.interfaces import (
    ChannelClientPort,
    ChannelInbound,
    ChannelOutbound,
    OrchestrationInput,
    OrchestratorPort,
    SessionStorePort,
    TenantPolicyPort,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class RouteInboundInput:
    """Input for routing inbound messages."""

    tenant_id: str
    channel: str
    user_id: str
    text: str
    metadata: dict


@dataclass(frozen=True)
class RouteInboundOutput:
    """Output for routing inbound messages."""

    session_id: str
    response_text: str
    allowed: bool


class RouteInboundUseCase:
    """Route inbound messages and deliver responses."""

    def __init__(
        self,
        orchestrator: OrchestratorPort,
        sessions: SessionStorePort,
        policy: TenantPolicyPort,
        channel: ChannelClientPort,
    ) -> None:
        self._orchestrator = orchestrator
        self._sessions = sessions
        self._policy = policy
        self._channel = channel

    async def execute(self, input_: RouteInboundInput) -> RouteInboundOutput:
        """Execute routing for inbound message."""
        inbound = self._inbound(input_)
        return await self._route(inbound)

    async def _route(self, inbound: ChannelInbound) -> RouteInboundOutput:
        """Route inbound message with policy checks."""
        if not self._allowed(inbound):
            return self._denied()
        return await self._allowed_route(inbound)

    async def _allowed_route(self, inbound: ChannelInbound) -> RouteInboundOutput:
        """Process allowed inbound messages."""
        session = self._session(inbound)
        output = await self._respond(inbound, session.id)
        await self._send(inbound, output)
        self._touch(session)
        return self._result(session.id, output, True)

    def _inbound(self, input_: RouteInboundInput) -> ChannelInbound:
        """Build inbound message object."""
        return ChannelInbound(
            input_.tenant_id, input_.channel, input_.user_id, input_.text, input_.metadata
        )

    def _allowed(self, inbound: ChannelInbound) -> bool:
        """Check policy for inbound message."""
        return self._policy.allow(inbound)

    def _denied(self) -> RouteInboundOutput:
        """Build denied response output."""
        return RouteInboundOutput("", "", False)

    def _session(self, inbound: ChannelInbound):
        """Get or create session for inbound message."""
        return self._sessions.get_or_create(inbound)

    async def _respond(self, inbound: ChannelInbound, session_id: str):
        """Invoke orchestrator to get response."""
        input_ = self._orchestration_input(inbound, session_id)
        output = await self._orchestrator.invoke(input_)
        return output.message

    def _orchestration_input(self, inbound: ChannelInbound, session_id: str):
        """Build orchestration input."""
        return OrchestrationInput(
            message=inbound.text,
            session_id=session_id,
            context=self._context(inbound),
        )

    def _context(self, inbound: ChannelInbound) -> dict:
        """Build context for orchestration."""
        return {
            "tenant_id": inbound.tenant_id,
            "channel": inbound.channel,
            "user_id": inbound.user_id,
            **(inbound.metadata or {}),
        }

    async def _send(self, inbound: ChannelInbound, text: str) -> None:
        """Send response to channel."""
        message = ChannelOutbound(
            inbound.tenant_id,
            inbound.channel,
            inbound.user_id,
            text,
            inbound.metadata,
        )
        await self._channel.send(message)

    def _touch(self, session) -> None:
        """Update session activity."""
        session.touch()
        self._sessions.save(session)

    def _result(self, session_id: str, text: str, allowed: bool) -> RouteInboundOutput:
        """Build use-case output."""
        return RouteInboundOutput(session_id, text, allowed)
