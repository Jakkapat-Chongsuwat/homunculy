"""Transport Ports - Abstract RTC transports.

These interfaces abstract the RTC transport layer so you can
swap WebRTC solutions or custom transports.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RoomConfig:
    """Room connection configuration."""

    url: str
    room: str
    token: str
    identity: str = "agent"


@dataclass(frozen=True)
class SessionConfig:
    """Session configuration."""

    session_id: str
    room: str
    user_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioFrame:
    """Audio data frame."""

    data: bytes
    sample_rate: int = 48000
    channels: int = 1


class RoomPort(ABC):
    """RTC room abstraction."""

    @abstractmethod
    async def connect(self, config: RoomConfig) -> None:
        """Connect to room."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from room."""
        ...

    @abstractmethod
    def on_audio(self, handler: Callable[[AudioFrame], None]) -> None:
        """Register audio frame handler."""
        ...

    @abstractmethod
    async def publish_audio(self, frame: AudioFrame) -> None:
        """Publish audio to room."""
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        ...


class TokenGeneratorPort(ABC):
    """Token generation for room access."""

    @abstractmethod
    def create_agent_token(self, room: str, identity: str) -> str:
        """Create token for agent to join room."""
        ...

    @abstractmethod
    def create_user_token(self, room: str, identity: str) -> str:
        """Create token for user to join room."""
        ...


class TransportServicePort(ABC):
    """Transport service lifecycle."""

    @abstractmethod
    def run(self) -> None:
        """Start transport service (blocking)."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Graceful shutdown."""
        ...
