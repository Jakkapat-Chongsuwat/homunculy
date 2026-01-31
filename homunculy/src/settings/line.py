"""LINE channel settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LineSettings(BaseSettings):
    """LINE Messaging API settings."""

    model_config = SettingsConfigDict(
        env_prefix="LINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    channel_access_token: str = Field(default="", description="LINE channel access token")
    api_base: str = Field(default="https://api.line.me", description="LINE API base URL")


line_settings = LineSettings()
