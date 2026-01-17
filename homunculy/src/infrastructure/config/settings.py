"""Application settings and configuration."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class AppSettings:
    """Application settings."""

    name: str = "homunculy"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class DatabaseSettings:
    """Database settings."""

    host: str = "localhost"
    port: int = 5432
    name: str = "homunculy"
    user: str = "postgres"
    password: str = ""


@dataclass
class LLMSettings:
    """LLM service settings."""

    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class TTSSettings:
    """TTS service settings."""

    provider: str = "elevenlabs"
    api_key: str = ""
    model_id: str = "eleven_multilingual_v2"
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"


@dataclass
class LiveKitSettings:
    """LiveKit settings."""

    url: str = ""
    api_key: str = ""
    api_secret: str = ""


@dataclass
class Settings:
    """All application settings."""

    app: AppSettings
    database: DatabaseSettings
    llm: LLMSettings
    tts: TTSSettings
    livekit: LiveKitSettings


@lru_cache
def get_settings() -> Settings:
    """Get cached settings from environment."""
    return Settings(
        app=_load_app_settings(),
        database=_load_database_settings(),
        llm=_load_llm_settings(),
        tts=_load_tts_settings(),
        livekit=_load_livekit_settings(),
    )


def _load_app_settings() -> AppSettings:
    """Load app settings from environment."""
    return AppSettings(
        name=os.getenv("APP_NAME", "homunculy"),
        version=os.getenv("APP_VERSION", "1.0.0"),
        debug=os.getenv("APP_DEBUG", "false").lower() == "true",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
    )


def _load_database_settings() -> DatabaseSettings:
    """Load database settings from environment."""
    return DatabaseSettings(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        name=os.getenv("DB_NAME", "homunculy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def _load_llm_settings() -> LLMSettings:
    """Load LLM settings from environment."""
    return LLMSettings(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        api_key=os.getenv("LLM_OPENAI_API_KEY", ""),
        model=os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "2000")),
    )


def _load_tts_settings() -> TTSSettings:
    """Load TTS settings from environment."""
    return TTSSettings(
        provider=os.getenv("TTS_PROVIDER", "elevenlabs"),
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        model_id=os.getenv("TTS_ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        voice_id=os.getenv("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
    )


def _load_livekit_settings() -> LiveKitSettings:
    """Load LiveKit settings from environment."""
    return LiveKitSettings(
        url=os.getenv("LIVEKIT_URL", ""),
        api_key=os.getenv("LIVEKIT_API_KEY", ""),
        api_secret=os.getenv("LIVEKIT_API_SECRET", ""),
    )
