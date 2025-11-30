"""
TTS Streaming Use Case - Stream text to audio in real-time.

Single Responsibility: Convert sentences to audio chunks and deliver via callback.
This is a use case that orchestrates TTS service calls and audio delivery.
"""

import asyncio
import re
from typing import Optional, Callable, Awaitable

from common.logger import get_logger
from settings.tts import tts_settings
from internal.domain.services import TTSService


logger = get_logger(__name__)


# Minimum chunk size to send (bytes)
# Small chunks can have incomplete MP3 frames causing "ah/uh" sounds
MIN_CHUNK_SIZE = 1024

# Regex to strip emojis and other symbols that TTS reads poorly
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical
    "\U0001F780-\U0001F7FF"  # geometric shapes extended
    "\U0001F800-\U0001F8FF"  # supplemental arrows-c
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
    "\U00002702-\U000027B0"  # dingbats
    "\U0001F1E0-\U0001F1FF"  # flags
    "]+",
    flags=re.UNICODE,
)


class TTSStreamingUseCaseImpl:
    """
    Use case for streaming text-to-speech conversion.

    Converts text sentences to audio chunks in real-time.
    Follows Clean Architecture: depends on domain service abstraction.
    """

    def __init__(
        self,
        tts_service: TTSService,
        voice_id: str,
        on_audio_chunk: Callable[[bytes, int, bool], Awaitable[None]],
    ) -> None:
        """
        Initialize TTS streaming use case.

        Args:
            tts_service: Domain TTS service abstraction
            voice_id: Voice ID for TTS provider
            on_audio_chunk: Callback for audio chunks (bytes, index, is_final)
        """
        self._tts = tts_service
        self._voice_id = voice_id
        self._on_audio_chunk = on_audio_chunk
        self._queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        self._chunk_index = 0
        self._chunks_sent = 0
        self._audio_buffer = bytearray()

    @property
    def chunks_sent(self) -> int:
        """Get count of audio chunks sent."""
        return self._chunks_sent

    @property
    def current_index(self) -> int:
        """Get current chunk index."""
        return self._chunk_index

    async def queue_sentence(self, sentence: str) -> None:
        """Queue a sentence for TTS processing."""
        await self._queue.put(sentence)

    async def finish(self) -> None:
        """Signal that no more sentences will be queued."""
        await self._queue.put(None)

    async def run(self) -> None:
        """Run the TTS worker loop."""
        while True:
            sentence = await self._queue.get()
            if sentence is None:
                break
            await self._process_sentence(sentence)

        await self._flush_buffer()

    async def _process_sentence(self, sentence: str) -> None:
        """Process a single sentence through TTS."""
        cleaned = self._strip_emojis(sentence)
        if not cleaned.strip():
            return

        try:
            await self._stream_sentence(cleaned)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("TTS error", error=str(e))

    def _strip_emojis(self, text: str) -> str:
        """Remove emojis and symbols that TTS reads poorly."""
        return EMOJI_PATTERN.sub("", text)

    async def _stream_sentence(self, sentence: str) -> None:
        """Stream TTS audio for a sentence."""
        logger.debug("TTS processing", text=sentence[:50])

        async for audio_chunk in self._tts.stream(
            text=sentence,
            voice_id=self._voice_id,
            model_id=tts_settings.elevenlabs_streaming_model_id,
        ):
            await self._buffer_chunk(audio_chunk)
            await asyncio.sleep(0.001)

    async def _buffer_chunk(self, audio_bytes: bytes) -> None:
        """Buffer audio and send when large enough."""
        self._audio_buffer.extend(audio_bytes)

        if len(self._audio_buffer) >= MIN_CHUNK_SIZE:
            await self._send_buffered()

    async def _send_buffered(self) -> None:
        """Send buffered audio and clear buffer."""
        if not self._audio_buffer:
            return

        self._chunk_index += 1
        self._chunks_sent += 1
        await self._on_audio_chunk(bytes(self._audio_buffer), self._chunk_index, False)
        self._audio_buffer.clear()

    async def _flush_buffer(self) -> None:
        """Flush any remaining audio in buffer."""
        if len(self._audio_buffer) > 0:
            await self._send_buffered()


def create_tts_streaming_usecase(
    tts_service: Optional[TTSService],
    voice_id: str,
    on_audio_chunk: Callable[[bytes, int, bool], Awaitable[None]],
) -> Optional[TTSStreamingUseCaseImpl]:
    """
    Factory function for creating TTS streaming use case.

    Args:
        tts_service: TTS service (None if not configured)
        voice_id: Voice ID for TTS
        on_audio_chunk: Callback for audio chunks

    Returns:
        TTSStreamingUseCaseImpl or None if TTS not configured
    """
    if tts_service is None:
        return None
    return TTSStreamingUseCaseImpl(tts_service, voice_id, on_audio_chunk)
