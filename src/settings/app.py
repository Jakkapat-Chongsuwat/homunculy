"""
Application-specific settings configuration.

This module contains settings related to the application itself,
such as name, version, server configuration, etc.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class ApplicationSettings(BaseSettings):
    """Main application settings."""

    name: str = Field(
        default="Pokédex API",
        description="Application name"
    )
    version: str = Field(
        default="3",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        gt=0,
        le=65535,
        description="Server port"
    )

    class Config:
        env_prefix = "APP_"


# Global instance
app_settings = ApplicationSettings()