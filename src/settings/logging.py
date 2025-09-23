"""
Logging configuration settings.

This module contains all logging-related configuration including
log levels, formatters, handlers, and output destinations.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    # Log Level
    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Log Format
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )

    # Date Format
    date_format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="Date format for log timestamps"
    )

    # File Logging
    file_enabled: bool = Field(
        default=True,
        description="Enable file logging"
    )
    file_path: str = Field(
        default="logs/app.log",
        description="Log file path"
    )
    file_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum log file size in bytes"
    )
    file_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )

    # Console Logging
    console_enabled: bool = Field(
        default=True,
        description="Enable console logging"
    )

    # Structured Logging (JSON)
    structured_enabled: bool = Field(
        default=False,
        description="Enable structured JSON logging"
    )

    class Config:
        env_prefix = "LOGGING_"


# Global instance
logging_settings = LoggingSettings()