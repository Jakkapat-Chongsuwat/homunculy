"""Session Handle - Manages individual agent sessions.

Extracted from livekit_worker.py for Single Responsibility.
Each session handle manages one room connection.

Clean Architecture: Uses ports, not concrete implementations.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

from common.logger import get_logger
from domain.interfaces import RoomConfig, RoomPort, SessionConfig, TokenGeneratorPort

if TYPE_CHECKING:
    from livekit.agents import Agent

logger = get_logger(__name__)

# Config from environment
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
AGENT_NAME = os.getenv("AGENT_NAME", "homunculy-super")


class AgentSessionHandle:
    """Handles a single agent session in a room.

    Uses ports for room and token generation - swappable implementations.
    """

    def __init__(
        self,
        config: SessionConfig,
        room_adapter: RoomPort,
        token_generator: TokenGeneratorPort,
    ) -> None:
        self._config = config
        self._room_adapter = room_adapter
        self._token_generator = token_generator
        self.status = "created"

    @property
    def session_id(self) -> str:
        return self._config.session_id

    @property
    def room(self) -> str:
        return self._config.room

    @property
    def user_id(self) -> str:
        return self._config.user_id

    @property
    def metadata(self) -> dict:
        return dict(self._config.metadata)

    async def run(self) -> None:
        """Connect and run agent session."""
        try:
            await self._connect()
            await self._run_pipeline()
        except Exception as e:
            self._set_error(e)
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Stop the session."""
        self.status = "stopping"
        await self._cleanup()

    async def _connect(self) -> None:
        """Connect to room using port."""
        self.status = "connecting"
        identity = f"agent-{self.session_id}"
        token = self._token_generator.create_agent_token(self.room, identity)
        config = RoomConfig(url=LIVEKIT_URL, room=self.room, token=token, identity=identity)
        await self._room_adapter.connect(config)
        self.status = "connected"
        logger.info("Joined room", room=self.room, session=self.session_id)

    async def _run_pipeline(self) -> None:
        """Run the STT/LLM/TTS pipeline."""
        if not self._room_adapter.is_connected:
            return
        session = _create_agent_session()
        agent = _create_agent(self)
        # Get native room for LiveKit AgentSession
        native_room = getattr(self._room_adapter, "native_room", None)
        if native_room:
            await session.start(agent=agent, room=native_room)

    def _set_error(self, e: Exception) -> None:
        """Set error state."""
        self.status = "error"
        logger.error("Session error", error=str(e), session=self.session_id)

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        await self._room_adapter.disconnect()
        self.status = "disconnected"


class SessionRegistry:
    """Registry for active sessions.

    Uses dependency injection for room and token adapters.
    """

    def __init__(
        self,
        room_factory: "Callable[[], RoomPort] | None" = None,
        token_generator: TokenGeneratorPort | None = None,
    ) -> None:
        self._sessions: dict[str, AgentSessionHandle] = {}
        self._room_factory = room_factory or _default_room_factory
        self._token_generator = token_generator or _default_token_generator()

    @property
    def count(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)

    def create(self, room: str, user_id: str, metadata: dict) -> AgentSessionHandle:
        """Create and register new session."""
        session_id = f"{room}-{uuid4().hex[:8]}"
        config = SessionConfig(
            session_id=session_id,
            room=room,
            user_id=user_id,
            metadata=metadata,
        )
        handle = AgentSessionHandle(
            config=config,
            room_adapter=self._room_factory(),
            token_generator=self._token_generator,
        )
        self._sessions[session_id] = handle
        return handle

    def remove(self, session_id: str) -> AgentSessionHandle | None:
        """Remove session from registry."""
        return self._sessions.pop(session_id, None)

    def list_all(self) -> list[dict]:
        """List all sessions."""
        return [_session_info(s) for s in self._sessions.values()]

    async def cleanup_all(self) -> None:
        """Cleanup all sessions."""
        for session in list(self._sessions.values()):
            await session.stop()
        self._sessions.clear()


# --- Default Factories (use container in production) ---


def _default_room_factory() -> RoomPort:
    """Default room factory using container."""
    from infrastructure.container import get_room

    return get_room()


def _default_token_generator() -> TokenGeneratorPort:
    """Default token generator using container."""
    from infrastructure.container import get_token_generator

    return get_token_generator()


def _create_agent_session():
    """Create LiveKit AgentSession."""
    from livekit.agents import AgentSession
    from livekit.plugins import openai, silero

    from infrastructure.config import get_settings

    settings = get_settings()
    return AgentSession(
        vad=silero.VAD.load(),
        llm=openai.LLM(model=settings.llm.model),
        stt=openai.STT(),
        tts=openai.TTS(voice="alloy"),
    )


def _create_supervisor(handle: AgentSessionHandle) -> "Agent":
    """Create supervisor agent using LiveKit adapter."""
    from agents.supervisor import SessionContext
    from infrastructure.adapters.transport.livekit_agents import create_livekit_supervisor
    from infrastructure.container import get_supervisor

    ctx = SessionContext(
        session_id=handle.session_id,
        user_id=handle.user_id,
        room=handle.room,
        personality=handle.metadata.get("personality", "default"),
    )
    supervisor_port = get_supervisor()
    return create_livekit_supervisor(ctx, supervisor_port)


def _create_companion(handle: AgentSessionHandle) -> "Agent":
    """Create companion agent using LiveKit adapter."""
    from agents.companion import CompanionContext
    from infrastructure.adapters.transport.livekit_agents import create_livekit_companion
    from infrastructure.container import get_orchestrator

    ctx = CompanionContext(
        session_id=handle.session_id,
        user_id=handle.user_id,
        name=handle.metadata.get("name", "Luna"),
        personality=handle.metadata.get("personality", "warm"),
    )
    orchestrator = get_orchestrator()
    return create_livekit_companion(ctx, orchestrator)


def _create_agent(handle: AgentSessionHandle) -> "Agent":
    """Create agent based on type in metadata."""
    agent_type = handle.metadata.get("agent_type", "companion")
    if agent_type == "supervisor":
        return _create_supervisor(handle)
    return _create_companion(handle)


def _session_info(s: AgentSessionHandle) -> dict:
    """Extract session info dict."""
    return {"session_id": s.session_id, "room": s.room, "status": s.status}
