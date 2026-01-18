"""OpenAI STT adapter implementing STTPort."""

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from common.logger import get_logger
from domain.interfaces import STTPort

logger = get_logger(__name__)


class OpenAISTTAdapter(STTPort):
    """OpenAI Whisper-based STT adapter."""

    def __init__(self, api_key: str, model: str = "whisper-1") -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        logger.info("OpenAI STT adapter initialized", model=model)

    async def transcribe(self, audio: bytes) -> str:
        """Transcribe audio to text."""
        logger.debug("Transcribing audio", size=len(audio))
        transcript = await self._do_transcribe(audio)
        logger.debug("Transcription complete", length=len(transcript))
        return transcript

    async def _do_transcribe(self, audio: bytes) -> str:
        """Execute transcription API call."""
        response = await self._client.audio.transcriptions.create(
            model=self._model,
            file=_wrap_audio(audio),
        )
        return response.text

    def stream_transcribe(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[str]:
        """Stream transcription from audio chunks."""
        return self._stream_impl(audio_stream)

    async def _stream_impl(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[str]:
        """Internal streaming implementation."""
        # OpenAI doesn't support true streaming STT
        # Collect audio and transcribe in batches
        buffer = b""
        async for chunk in audio_stream:
            buffer += chunk
            if len(buffer) >= _CHUNK_THRESHOLD:
                yield await self.transcribe(buffer)
                buffer = b""
        if buffer:
            yield await self.transcribe(buffer)


def _wrap_audio(audio: bytes):
    """Wrap audio bytes for API upload."""
    import io

    return ("audio.wav", io.BytesIO(audio), "audio/wav")


# Minimum bytes before transcribing
_CHUNK_THRESHOLD = 16000 * 2 * 3  # ~3 seconds at 16kHz mono 16-bit
