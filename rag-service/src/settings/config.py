"""
Main configuration module.

Combines all service settings into a single configuration object.
"""

import os

try:
    import dotenv

    dotenv.load_dotenv()
except ImportError:
    pass

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")

    name: str = "rag-service"
    version: str = "1.0.0"
    debug: bool = (
        os.getenv(
            "APP_DEBUG",
            "false",
        ).lower()
        == "true"
    )
    host: str = os.getenv(
        "APP_HOST",
        "0.0.0.0",
    )
    port: int = int(
        os.getenv(
            "APP_PORT",
            "8001",
        )
    )


app_settings = ApplicationSettings()

APP_NAME = app_settings.name
APP_VERSION = app_settings.version


class Settings(BaseSettings):
    """Root settings combining all configurations."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app: ApplicationSettings = app_settings


settings = Settings()
