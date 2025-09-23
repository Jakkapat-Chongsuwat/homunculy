"""
Settings module for the application.

This module provides centralized configuration management using Pydantic BaseSettings
for type-safe configuration with environment variable support.
"""

from .config import settings

# Application settings
APP_NAME = settings.app.name
APP_VERSION = settings.app.version

# Database settings
DATABASE_URI = settings.database.uri
SQLALCHEMY_ECHO = settings.database.echo
SQLALCHEMY_ISOLATION_LEVEL = settings.database.isolation_level

# LLM settings
OPENAI_API_KEY = settings.llm.openai_api_key
LLM_DEFAULT_MODEL = settings.llm.default_model
LLM_DEFAULT_TEMPERATURE = settings.llm.default_temperature
LLM_DEFAULT_MAX_TOKENS = settings.llm.default_max_tokens

# Security settings
JWT_SECRET_KEY = settings.security.jwt_secret_key
JWT_ALGORITHM = settings.security.jwt_algorithm
JWT_EXPIRATION_HOURS = settings.security.jwt_expiration_hours

# Logging settings
LOG_LEVEL = settings.logging.level
LOG_FORMAT = settings.logging.format
LOG_DATE_FORMAT = settings.logging.date_format

# Export the settings instance and individual service settings for direct access
__all__ = [
    "settings",
    # Application
    "APP_NAME",
    "APP_VERSION",
    # Database
    "DATABASE_URI",
    "SQLALCHEMY_ECHO",
    "SQLALCHEMY_ISOLATION_LEVEL",
    # LLM
    "OPENAI_API_KEY",
    "LLM_DEFAULT_MODEL",
    "LLM_DEFAULT_TEMPERATURE",
    "LLM_DEFAULT_MAX_TOKENS",
    # Security
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "JWT_EXPIRATION_HOURS",
    # Logging
    "LOG_LEVEL",
    "LOG_FORMAT",
    "LOG_DATE_FORMAT",
]
