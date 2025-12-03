"""
TTS (Text-to-Speech) service configuration.

Manages configuration for text-to-speech services supporting multiple providers.
"""

import os
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


TTSProvider = Literal["elevenlabs", "azure", "google", "aws"]


class TTSSettings(BaseSettings):
    """Text-to-Speech service configuration."""

    model_config = SettingsConfigDict(
        env_prefix="TTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider Selection
    provider: TTSProvider = Field(default="elevenlabs", description="TTS provider to use")

    # ElevenLabs Configuration
    elevenlabs_api_key: Optional[str] = Field(default=None, description="ElevenLabs API key")
    elevenlabs_model_id: str = Field(
        default="eleven_multilingual_v2", description="Default ElevenLabs TTS model"
    )
    elevenlabs_streaming_model_id: str = Field(
        default="eleven_turbo_v2_5", description="Fast model for WebSocket streaming"
    )
    elevenlabs_output_format: str = Field(
        default="pcm_24000",
        description="Output format: pcm_24000 for iOS compatibility, mp3_44100_128 for desktop",
    )

    # Azure TTS Configuration (future)
    azure_api_key: Optional[str] = Field(default=None, description="Azure Speech Services API key")
    azure_region: str = Field(default="eastus", description="Azure region")

    # Google TTS Configuration (future)
    google_credentials_path: Optional[str] = Field(
        default=None, description="Path to Google Cloud credentials JSON"
    )

    # AWS Polly Configuration (future)
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    aws_region: str = Field(default="us-east-1", description="AWS region")

    # Default voice settings (provider-agnostic)
    default_voice_id: str = Field(
        default="EXAVITQu4vr4xnSDxMaL", description="Default voice ID (provider-specific)"
    )
    default_stability: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Voice stability (0.0-1.0)"
    )
    default_similarity_boost: float = Field(
        default=0.75, ge=0.0, le=1.0, description="Voice similarity boost (0.0-1.0)"
    )
    default_style: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Voice style exaggeration (0.0-1.0)"
    )
    default_use_speaker_boost: bool = Field(default=True, description="Enable speaker boost")


# Global TTS settings instance
tts_settings = TTSSettings(
    elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY") or os.getenv("TTS_ELEVENLABS_API_KEY"),
)
