"""
Security and authentication configuration settings.

This module contains all security-related configuration including
API keys, JWT settings, CORS configuration, and authentication options.
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        extra="ignore",
    )

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token signing",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, gt=0, description="JWT token expiration in hours")

    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")

    # API Key Authentication
    api_key_header_name: str = Field(
        default="X-API-Key", description="Header name for API key authentication"
    )
    api_keys: List[str] = Field(default=[], description="List of valid API keys")

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100, gt=0, description="Number of requests allowed per time window"
    )
    rate_limit_window_seconds: int = Field(
        default=60, gt=0, description="Rate limit time window in seconds"
    )


# Global instance
security_settings = SecuritySettings()
