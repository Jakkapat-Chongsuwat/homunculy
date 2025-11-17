"""
LLM (Large Language Model) configuration settings.

This module contains all LLM-related configuration including
API keys, model settings, and provider-specific options.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class PydanticSettings(BaseSettings):
    """LLM (Large Language Model) configuration settings."""

    # API Keys - PydanticAI uses OpenAI's API, so we only need OpenAI key
    openai_api_key: str = Field(
        default="sk-test-openai-dummy-key",
        description="OpenAI API key (used by both OpenAI and PydanticAI providers)"
    )

    # Default Model Configuration
    default_model: str = Field(
        default="gpt-4",
        description="Default LLM model to use"
    )
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for LLM responses"
    )
    default_max_tokens: int = Field(
        default=1000,
        gt=0,
        description="Default maximum tokens for LLM responses"
    )

    # Provider-specific settings
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )

    # Rate limiting and timeouts
    request_timeout: int = Field(
        default=30,
        gt=0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of retries for failed requests"
    )

    class Config:
        env_prefix = "LLM_"
        validate_by_name = True


# Global instance
llm_settings = PydanticSettings()