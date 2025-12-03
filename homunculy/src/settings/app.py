"""
Application-specific settings configuration.

This module contains settings related to the application itself,
such as name, version, server configuration, etc.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = Field(default="Homunculy", description="Application name")
    version: str = Field(default="3.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, gt=0, le=65535, description="Server port")


# Global instance
app_settings = ApplicationSettings()
