"""Database configuration settings - simplified for Clean Architecture."""

from typing import Literal, Optional
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


DatabaseProvider = Literal["postgresql", "sqlite", "mysql"]


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Provider Selection
    provider: DatabaseProvider = Field(default="postgresql", description="Database provider to use")

    # PostgreSQL specific settings (primary for Aspire)
    postgres_host: str = Field(default="postgres", alias="DB_HOST", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, alias="DB_PORT", description="PostgreSQL port")
    postgres_db: str = Field(
        default="homunculy", alias="DB_NAME", description="PostgreSQL database name"
    )
    postgres_user: str = Field(
        default="homunculy", alias="DB_USER", description="PostgreSQL username"
    )
    postgres_password: str = Field(
        default="homunculy", alias="DB_PASSWORD", description="PostgreSQL password"
    )

    # SSL mode for cloud databases (Azure PostgreSQL requires SSL)
    postgres_sslmode: str = Field(
        default="prefer",
        alias="DB_SSLMODE",
        description="PostgreSQL SSL mode (disable, prefer, require)",
    )

    # Connection URI (can be set directly or computed)
    uri_override: Optional[str] = Field(
        default=None,
        alias="DATABASE_URI",
        description="Database connection string (overrides computed URI)",
    )

    @computed_field
    @property
    def uri(self) -> str:
        """Compute database URI from components or use override."""
        if self.uri_override:
            return self.uri_override
        encoded_password = quote_plus(self.postgres_password)
        base_uri = f"postgresql+asyncpg://{self.postgres_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        if self.postgres_sslmode != "disable":
            # asyncpg (used by SQLAlchemy async engine) supports `ssl` kwarg, not `sslmode`.
            # For psycopg connections (e.g., LangGraph checkpointer), we translate `ssl` -> `sslmode`
            # at the call site.
            return f"{base_uri}?ssl={self.postgres_sslmode}"
        return base_uri

    # SQLite specific settings
    sqlite_path: str = Field(default=":memory:", description="SQLite database file path")

    # MySQL specific settings (future)
    mysql_host: Optional[str] = Field(default=None, description="MySQL host")
    mysql_port: int = Field(default=3306, description="MySQL port")

    # General settings
    echo: bool = Field(default=False, description="Enable SQL statement logging")
    isolation_level: str = Field(default="SERIALIZABLE", description="Database isolation level")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum overflow connections")


database_settings = DatabaseSettings()
