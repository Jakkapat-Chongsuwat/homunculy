"""Database configuration settings - simplified for Clean Architecture."""

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
        """Pydantic config."""
        env_prefix = "DATABASE_"


database_settings = DatabaseSettings()