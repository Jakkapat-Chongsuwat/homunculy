"""STT service port (interface)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class STTPort(ABC):
    """Speech-to-text interactions contract."""

    @abstractmethod
    async def transcribe(self, audio: bytes) -> str:
        """Transcribe audio to text."""
        ...

    @abstractmethod
    def stream_transcribe(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[str]:
        """Stream transcription from audio chunks."""
        ...
