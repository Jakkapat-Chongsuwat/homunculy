"""
Chat Client Configuration.

Central place for all configurable values.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ServerConfig:
    """WebSocket server configuration."""

    uri: str = "ws://localhost:8000/api/v1/ws/chat"


@dataclass(frozen=True)
class AudioConfig:
    """Audio playback configuration."""

    sample_rate: int = 44100
    channels: int = 1
    sample_width: int = 2
    min_buffer_size: int = 16384
    pre_buffer_size: int = 44100
    volume_boost: int = 6
    frame_buffer: int = 4096


@dataclass(frozen=True)
class AgentConfig:
    """AI agent configuration."""

    provider: str = "langraph"
    model_name: str = "gpt-4o-mini"
    voice_id: str = "lhTvHflPVOqgSWyuWQry"
    temperature: float = 0.7
    max_tokens: int = 500
    personality_name: str = "Homunculy"
    personality_description: str = "A friendly AI assistant"
    personality_mood: str = "cheerful"
    system_prompt: str = (
        "You are Homunculy, a friendly AI assistant. "
        "Respond directly to the user's message. Be concise. "
        "Never summarize previous conversations. "
        "If interrupted, just respond to the new message naturally."
    )


# Global config instances
SERVER = ServerConfig()
AUDIO = AudioConfig()
AGENT = AgentConfig()
