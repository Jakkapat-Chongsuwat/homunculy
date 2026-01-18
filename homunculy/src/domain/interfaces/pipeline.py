"""
Pipeline Ports - Abstract STT/LLM/TTS pipeline.

These interfaces abstract the voice processing pipeline so you can
swap OpenAI for other providers or custom implementations.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline configuration."""

    model: str = "gpt-4o-mini"
    voice: str = "alloy"
    language: str = "en"
    vad_threshold: float = 0.5


@dataclass
class TranscriptionResult:
    """Speech-to-text result."""

    text: str
    confidence: float = 1.0
    is_final: bool = True
    language: str = "en"


@dataclass
class SynthesisResult:
    """Text-to-speech result."""

    audio: bytes
    sample_rate: int = 24000
    duration_ms: int = 0


class VoiceActivityDetectorPort(ABC):
    """Detects speech in audio."""

    @abstractmethod
    async def detect(self, audio: bytes) -> bool:
        """Detect if audio contains speech."""
        ...

    @abstractmethod
    def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Stream audio, yielding only speech segments."""
        ...


class SpeechToTextPort(ABC):
    """Transcribes audio to text."""

    @abstractmethod
    async def transcribe(self, audio: bytes, language: str = "en") -> TranscriptionResult:
        """Transcribe audio to text."""
        ...

    @abstractmethod
    def stream(self, audio: AsyncIterator[bytes]) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription results."""
        ...


class TextToSpeechPort(ABC):
    """Synthesizes text to audio."""

    @abstractmethod
    async def synthesize(self, text: str, voice: str = "alloy") -> SynthesisResult:
        """Synthesize text to audio."""
        ...

    @abstractmethod
    def stream(self, text: str, voice: str = "alloy") -> AsyncIterator[bytes]:
        """Stream audio chunks."""
        ...


class PipelinePort(ABC):
    """Orchestrates full voice pipeline: VAD → STT → LLM → TTS."""

    @abstractmethod
    async def process_audio(self, audio: bytes) -> SynthesisResult:
        """Process audio input through full pipeline."""
        ...

    @abstractmethod
    def stream_audio(self, audio: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Stream audio through pipeline."""
        ...

    @abstractmethod
    async def interrupt(self) -> None:
        """Interrupt current processing."""
        ...
