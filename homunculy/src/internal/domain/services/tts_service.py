"""TTS service contract."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class TTSService(ABC):
    """Text-to-speech interactions contract."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None,
    ) -> bytes:
        """Synthesize text to speech."""
        pass

    @abstractmethod
    def stream(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None,
    ) -> AsyncIterator[bytes]:
        """Stream TTS audio chunks."""
        pass

    @abstractmethod
    async def get_voices(self) -> list[dict]:
        """Return available voices."""
        pass
