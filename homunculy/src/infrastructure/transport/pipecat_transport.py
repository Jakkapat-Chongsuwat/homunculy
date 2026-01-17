"""Pipecat transport configuration for WebRTC."""

from dataclasses import dataclass
from typing import Any

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.transports.livekit.transport import LiveKitParams, LiveKitTransport


@dataclass
class TransportConfig:
    """Transport configuration options."""

    audio_out: bool = True
    audio_in: bool = True
    camera_in: bool = False
    vad_enabled: bool = True
    vad_passthrough: bool = True


def create_livekit_transport(
    url: str,
    token: str,
    room: str,
    config: TransportConfig | None = None,
) -> LiveKitTransport:
    """Create LiveKit transport with configuration."""
    cfg = config or TransportConfig()
    params = _build_params(cfg)
    return LiveKitTransport(url, token, room, params=params)


def _build_params(cfg: TransportConfig) -> LiveKitParams:
    """Build LiveKit params from config."""
    return LiveKitParams(
        audio_out_enabled=cfg.audio_out,
        audio_in_enabled=cfg.audio_in,
        camera_in_enabled=cfg.camera_in,
        vad_enabled=cfg.vad_enabled,
        vad_analyzer=_create_vad() if cfg.vad_enabled else None,
        vad_audio_passthrough=cfg.vad_passthrough,
    )


def _create_vad() -> SileroVADAnalyzer:
    """Create VAD analyzer."""
    return SileroVADAnalyzer()


def extract_livekit_parts(ctx: Any) -> tuple[str, str, str]:
    """Extract URL, token, room from JobContext."""
    return _get_url(ctx), _get_token(ctx), _get_room(ctx)


def _get_url(ctx: Any) -> str:
    """Extract LiveKit URL from context."""
    return getattr(getattr(ctx, "_info", None), "url", "")


def _get_token(ctx: Any) -> str:
    """Extract LiveKit token from context."""
    return getattr(getattr(ctx, "_info", None), "token", "")


def _get_room(ctx: Any) -> str:
    """Extract room name from context."""
    return getattr(getattr(ctx, "room", None), "name", "")
