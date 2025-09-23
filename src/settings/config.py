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

from .app import app_settings, ApplicationSettings
from .database import database_settings, DatabaseSettings
from .pydantic import llm_settings, PydanticSettings
from .security import security_settings, SecuritySettings
from .logging import logging_settings, LoggingSettings

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Root settings class that combines all configuration."""

    app: ApplicationSettings = app_settings
    database: DatabaseSettings = database_settings
    llm: PydanticSettings = llm_settings
    security: SecuritySettings = security_settings
    logging: LoggingSettings = logging_settings

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()