"""Database configuration settings - simplified for Clean Architecture."""

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


DatabaseProvider = Literal["postgresql", "sqlite", "mysql"]


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # Provider Selection
    provider: DatabaseProvider = Field(
        default="postgresql",
        description="Database provider to use"
    )

    # Connection URI (primary configuration method)
    uri: str = Field(
        default="postgresql+asyncpg://homunculy:homunculy@postgres:5432/homunculy",
        description="Database connection string"
    )
    
    # PostgreSQL specific settings
    postgres_host: str = Field(
        default="postgres",
        description="PostgreSQL host"
    )
    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port"
    )
    postgres_db: str = Field(
        default="homunculy",
        description="PostgreSQL database name"
    )
    postgres_user: str = Field(
        default="homunculy",
        description="PostgreSQL username"
    )
    postgres_password: str = Field(
        default="homunculy",
        description="PostgreSQL password"
    )
    
    # SQLite specific settings
    sqlite_path: str = Field(
        default=":memory:",
        description="SQLite database file path"
    )
    
    # MySQL specific settings (future)
    mysql_host: Optional[str] = Field(
        default=None,
        description="MySQL host"
    )
    mysql_port: int = Field(
        default=3306,
        description="MySQL port"
    )
    
    # General settings
    echo: bool = Field(
        default=False,
        description="Enable SQL statement logging"
    )
    isolation_level: str = Field(
        default="SERIALIZABLE",
        description="Database isolation level"
    )
    pool_size: int = Field(
        default=5,
        description="Connection pool size"
    )
    max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections"
    )

    class Config:
        """Pydantic config."""
        env_prefix = "DATABASE_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


database_settings = DatabaseSettings()