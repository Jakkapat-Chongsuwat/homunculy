"""ElevenLabs TTS adapter implementing TTSPort."""

from collections.abc import AsyncIterator
from typing import Any

from common.logger import get_logger
from domain.interfaces import TTSPort
from elevenlabs.client import AsyncElevenLabs

from infrastructure.adapters.elevenlabs.helpers import (
    collect_audio,
    map_voices,
    stream_config,
    stream_generator,
    synth_config,
    synthesis_generator,
)

logger = get_logger(__name__)


class ElevenLabsTTSAdapter(TTSPort):
    """ElevenLabs implementation of TTS port."""

    def __init__(self, api_key: str) -> None:
        self._client = AsyncElevenLabs(api_key=api_key)
        logger.info("ElevenLabs TTS adapter initialized")

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        options: dict[str, Any] | None = None,
    ) -> bytes:
        """Synthesize text to speech audio."""
        config = _build_synth_config(options)
        return await self._do_synthesize(text, voice_id, config)

    async def _do_synthesize(self, text: str, voice_id: str, config: dict) -> bytes:
        """Execute synthesis with error handling."""
        _log_synth_start(voice_id, text, config)
        audio = await collect_audio(synthesis_generator(self._client, text, voice_id, config))
        _log_synth_done(voice_id, audio)
        return audio

    def stream(
        self,
        text: str,
        voice_id: str,
        options: dict[str, Any] | None = None,
    ) -> AsyncIterator[bytes]:
        """Stream TTS audio chunks."""
        config = _build_stream_config(options)
        _log_stream_start(voice_id, text, config)
        return stream_generator(self._client, text, voice_id, config)

    async def list_voices(self) -> list[dict[str, Any]]:
        """Return available voices."""
        response = await self._client.voices.get_all()
        voices = map_voices(response)
        logger.info("Voices fetched", count=len(voices))
        return voices


def _build_synth_config(options: dict | None) -> dict:
    """Build synthesis config from options."""
    opts = options or {}
    return synth_config(
        opts.get("model_id"),
        opts.get("stability"),
        opts.get("similarity_boost"),
        opts.get("style"),
        opts.get("use_speaker_boost"),
    )


def _build_stream_config(options: dict | None) -> dict:
    """Build stream config from options."""
    opts = options or {}
    return stream_config(
        opts.get("model_id"),
        opts.get("stability"),
        opts.get("similarity_boost"),
        opts.get("style"),
        opts.get("use_speaker_boost"),
    )


def _log_synth_start(voice_id: str, text: str, config: dict) -> None:
    """Log synthesis start."""
    logger.info("Synthesizing", voice_id=voice_id, model=config["model_id"], len=len(text))


def _log_synth_done(voice_id: str, audio: bytes) -> None:
    """Log synthesis completion."""
    logger.info("Synthesis done", voice_id=voice_id, size=len(audio))


def _log_stream_start(voice_id: str, text: str, config: dict) -> None:
    """Log stream start."""
    logger.info("Streaming TTS", voice_id=voice_id, model=config["model_id"], len=len(text))
