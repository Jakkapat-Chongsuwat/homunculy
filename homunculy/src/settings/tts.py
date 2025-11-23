"""
TTS (Text-to-Speech) service configuration.

Manages configuration for text-to-speech services like ElevenLabs.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class TTSSettings(BaseSettings):
    """Text-to-Speech service configuration."""

    # ElevenLabs Configuration
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_model_id: str = "eleven_monolingual_v1"
    
    # Default voice settings
    default_stability: float = 0.5
    default_similarity_boost: float = 0.75

    class Config:
        env_prefix = ""  # No prefix, read directly from env
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore other env vars


# Global TTS settings instance
tts_settings = TTSSettings(
    elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
)
