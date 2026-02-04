"""
OpenAI Pipeline Adapter.

Implements PipelinePort using OpenAI APIs via LiveKit plugins.
Can be swapped for other providers in the future.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from common.logger import get_logger
from domain.interfaces.pipeline import (
    PipelinePort,
    SpeechToTextPort,
    SynthesisResult,
    TextToSpeechPort,
    TranscriptionResult,
    VoiceActivityDetectorPort,
)

logger = get_logger(__name__)


class SileroVAD(VoiceActivityDetectorPort):
    """Silero VAD implementation."""

    def __init__(self, threshold: float = 0.5) -> None:
        self._threshold = threshold
        self._vad: Any = None

    async def detect(self, audio: bytes) -> bool:
        """Detect speech in audio."""
        _ = self._get_vad()  # Ensure loaded
        # Silero VAD would process audio here
        return True  # Simplified for now

    async def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Stream audio, yielding speech segments."""
        async for chunk in audio:
            if await self.detect(chunk):
                yield chunk

    def _get_vad(self) -> Any:
        """Lazy load VAD model."""
        if not self._vad:
            from livekit.plugins import silero

            self._vad = silero.VAD.load()
        return self._vad


class OpenAISTT(SpeechToTextPort):
    """OpenAI Whisper STT implementation."""

    def __init__(self, model: str = "whisper-1") -> None:
        self._model = model
        self._stt: Any = None

    async def transcribe(self, audio: bytes, language: str = "en") -> TranscriptionResult:
        """Transcribe audio to text."""
        # LiveKit plugin handles this
        return TranscriptionResult(text="", is_final=True)

    async def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription results."""
        async for chunk in audio:
            result = await self.transcribe(chunk)
            yield result

    def get_plugin(self) -> Any:
        """Get LiveKit STT plugin."""
        if not self._stt:
            from livekit.plugins import openai

            self._stt = openai.STT()
        return self._stt


class OpenAITTS(TextToSpeechPort):
    """OpenAI TTS implementation."""

    def __init__(self, voice: str = "alloy") -> None:
        self._voice = voice
        self._tts: Any = None

    async def synthesize(self, text: str, voice: str = "alloy") -> SynthesisResult:
        """Synthesize text to audio."""
        return SynthesisResult(audio=b"", sample_rate=24000)

    async def stream(self, text: str, voice: str = "alloy") -> AsyncIterator[bytes]:
        """Stream audio chunks."""
        result = await self.synthesize(text, voice)
        yield result.audio

    def get_plugin(self) -> Any:
        """Get LiveKit TTS plugin."""
        if not self._tts:
            from livekit.plugins import openai

            self._tts = openai.TTS(voice=self._voice)
        return self._tts


class OpenAIPipeline(PipelinePort):
    """Full pipeline using OpenAI components."""

    def __init__(
        self,
        vad: VoiceActivityDetectorPort,
        stt: SpeechToTextPort,
        tts: TextToSpeechPort,
    ) -> None:
        self._vad = vad
        self._stt = stt
        self._tts = tts
        self._interrupted = False

    async def process_audio(self, audio: bytes) -> SynthesisResult:
        """Process audio through pipeline."""
        # VAD → STT → LLM → TTS (simplified)
        transcription = await self._stt.transcribe(audio)
        return await self._tts.synthesize(transcription.text)

    async def stream_audio(self, audio: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Stream audio through pipeline."""
        async for chunk in audio:
            if self._interrupted:
                break
            result = await self.process_audio(chunk)
            yield result.audio

    async def interrupt(self) -> None:
        """Interrupt current processing."""
        self._interrupted = True


def create_openai_pipeline(voice: str = "alloy") -> OpenAIPipeline:
    """Factory to create OpenAI pipeline."""
    return OpenAIPipeline(
        vad=SileroVAD(),
        stt=OpenAISTT(),
        tts=OpenAITTS(voice=voice),
    )
