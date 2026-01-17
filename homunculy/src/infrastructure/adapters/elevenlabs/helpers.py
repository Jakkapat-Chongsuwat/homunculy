"""ElevenLabs helper functions."""

import os
from collections.abc import AsyncIterator
from typing import Any

from elevenlabs import VoiceSettings


def coalesce(value: Any | None, default: Any) -> Any:
    """Return value if not None, else default."""
    return value if value is not None else default


def synth_config(
    model_id: str | None,
    stability: float | None,
    similarity_boost: float | None,
    style: float | None,
    use_speaker_boost: bool | None,
) -> dict[str, Any]:
    """Build synthesis configuration."""
    return {
        "model_id": model_id or _default_model_id(),
        "stability": coalesce(stability, 0.5),
        "similarity_boost": coalesce(similarity_boost, 0.75),
        "style": coalesce(style, 0.0),
        "use_speaker_boost": coalesce(use_speaker_boost, True),
    }


def stream_config(
    model_id: str | None,
    stability: float | None,
    similarity_boost: float | None,
    style: float | None,
    use_speaker_boost: bool | None,
) -> dict[str, Any]:
    """Build streaming configuration."""
    config = synth_config(model_id, stability, similarity_boost, style, use_speaker_boost)
    config["model_id"] = model_id or _default_streaming_model_id()
    return config


def voice_settings(config: dict[str, Any]) -> VoiceSettings:
    """Create VoiceSettings from config."""
    return VoiceSettings(
        stability=config["stability"],
        similarity_boost=config["similarity_boost"],
        style=config["style"],
        use_speaker_boost=config["use_speaker_boost"],
    )


def synthesis_generator(client: Any, text: str, voice_id: str, config: dict) -> Any:
    """Create synthesis generator."""
    return client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=config["model_id"],
        voice_settings=voice_settings(config),
    )


def stream_generator(client: Any, text: str, voice_id: str, config: dict) -> Any:
    """Create stream generator."""
    return client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=config["model_id"],
        voice_settings=voice_settings(config),
    )


async def collect_audio(generator: AsyncIterator[bytes]) -> bytes:
    """Collect all audio chunks into bytes."""
    audio = b""
    async for chunk in generator:
        audio += chunk
    return audio


def map_voices(response: Any) -> list[dict]:
    """Map voice response to dict list."""
    return [_voice_to_dict(v) for v in response.voices]


def _voice_to_dict(voice: Any) -> dict:
    """Convert voice object to dict."""
    return {
        "voice_id": voice.voice_id,
        "name": voice.name,
        "category": voice.category,
        "description": voice.description,
        "labels": voice.labels,
    }


def _default_model_id() -> str:
    """Get default model ID."""
    return os.getenv("TTS_ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")


def _default_streaming_model_id() -> str:
    """Get default streaming model ID."""
    return os.getenv("TTS_ELEVENLABS_STREAMING_MODEL_ID", "eleven_turbo_v2_5")
