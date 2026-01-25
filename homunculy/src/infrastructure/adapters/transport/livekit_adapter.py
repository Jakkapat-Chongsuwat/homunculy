"""
LiveKit Transport Adapter.

Implements TransportPort using LiveKit SDK.
Can be swapped for other WebRTC solutions in the future.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from livekit import api, rtc

from common.logger import get_logger
from domain.interfaces.transport import (
    AudioFrame,
    RoomConfig,
    RoomPort,
    TokenGeneratorPort,
)

logger = get_logger(__name__)

# Config from environment
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")


class LiveKitRoom(RoomPort):
    """LiveKit implementation of RoomPort."""

    def __init__(self) -> None:
        self._room: rtc.Room | None = None
        self._audio_handler: Callable[[AudioFrame], None] | None = None

    @property
    def native_room(self) -> rtc.Room | None:
        """Get native LiveKit room for framework integration."""
        return self._room

    async def connect(self, config: RoomConfig) -> None:
        """Connect to LiveKit room."""
        self._room = rtc.Room()
        await self._room.connect(config.url, config.token)
        logger.info("Connected to room", room=config.room)

    async def disconnect(self) -> None:
        """Disconnect from room."""
        if self._room:
            await self._room.disconnect()
            self._room = None

    def on_audio(self, handler: Callable[[AudioFrame], None]) -> None:
        """Register audio frame handler."""
        self._audio_handler = handler

    async def publish_audio(self, frame: AudioFrame) -> None:
        """Publish audio to room."""
        if not self._room:
            return
        # LiveKit audio publish logic would go here
        # This is a simplified version
        logger.debug("Publishing audio", size=len(frame.data))

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        if not self._room:
            return False
        # Use enum comparison instead of string
        return self._room.connection_state == rtc.ConnectionState.CONN_CONNECTED


class LiveKitTokenGenerator(TokenGeneratorPort):
    """LiveKit token generator."""

    def __init__(self, api_key: str = "", api_secret: str = "") -> None:
        self._api_key = api_key or LIVEKIT_API_KEY
        self._api_secret = api_secret or LIVEKIT_API_SECRET

    def create_agent_token(self, room: str, identity: str) -> str:
        """Create agent token."""
        return self._create(room, identity, _agent_grants(room))

    def create_user_token(self, room: str, identity: str) -> str:
        """Create user token."""
        return self._create(room, identity, _user_grants(room))

    def _create(self, room: str, identity: str, grants: api.VideoGrants) -> str:
        """Create token with grants."""
        return (
            api.AccessToken(self._api_key, self._api_secret)
            .with_identity(identity)
            .with_grants(grants)
            .to_jwt()
        )


# --- Grant Helpers ---


def _agent_grants(room: str) -> api.VideoGrants:
    """Agent grants - full room access."""
    return api.VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        agent=True,
    )


def _user_grants(room: str) -> api.VideoGrants:
    """User grants - limited access."""
    return api.VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True,
    )
