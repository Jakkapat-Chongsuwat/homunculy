"""
Database configuration settings.

This module contains all database-related configuration including
connection strings, engine settings, and database-specific options.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    uri: str = Field(
        default="sqlite+aiosqlite:///:memory:",
        description="Database connection string"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL statement logging"
    )
    isolation_level: str = Field(
        default="SERIALIZABLE",
        description="Database isolation level"
    )

    class Config:
        env_prefix = "DATABASE_"


# Global instance
database_settings = DatabaseSettings()