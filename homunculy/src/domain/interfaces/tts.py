"""TTS service port (interface)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class TTSPort(ABC):
    """Text-to-speech interactions contract."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        options: dict[str, Any] | None = None,
    ) -> bytes:
        """Synthesize text to speech audio."""
        ...

    @abstractmethod
    def stream(
        self,
        text: str,
        voice_id: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[bytes]:
        """Stream TTS audio chunks."""
        ...

    @abstractmethod
    async def list_voices(self) -> list[dict[str, Any]]:
        """Return available voices."""
        ...
