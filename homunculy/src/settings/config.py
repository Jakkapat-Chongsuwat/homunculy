"""
Main configuration module that combines all service settings.

This module provides a centralized configuration system by importing
and combining all individual service configuration modules.
"""

# Load environment variables from .env file BEFORE importing settings
try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system environment variables

from pydantic_settings import BaseSettings, SettingsConfigDict

from .app import ApplicationSettings, app_settings
from .database import DatabaseSettings, database_settings
from .llm import LLMSettings, llm_settings
from .logging import LoggingSettings, logging_settings
from .security import SecuritySettings, security_settings
from .tts import TTSSettings, tts_settings


class Settings(BaseSettings):
    """Root settings class that combines all configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app: ApplicationSettings = app_settings
    database: DatabaseSettings = database_settings
    llm: LLMSettings = llm_settings
    security: SecuritySettings = security_settings
    logging: LoggingSettings = logging_settings
    tts: TTSSettings = tts_settings


# Global settings instance
settings = Settings()
