"""Gateway settings."""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Gateway configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    use_sqlite: bool = Field(default_factory=lambda: os.name == "nt")
    sqlite_file: str = Field(default=".homunculy.sqlite", description="SQLite session file")
    redis_embedded: bool = Field(default=False, description="Use embedded Redis (redislite)")
    redis_file: str = Field(default=".homunculy-redis.db", description="Embedded Redis data file")


gateway_settings = GatewaySettings()
