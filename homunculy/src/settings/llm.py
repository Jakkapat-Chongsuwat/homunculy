"""
LLM (Large Language Model) configuration settings.

This module contains all LLM-related configuration including
API keys, model settings, and provider-specific options.
"""

from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


LLMProvider = Literal["openai", "anthropic", "azure", "google"]


class LLMSettings(BaseSettings):
    """LLM (Large Language Model) configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Provider Selection
    provider: LLMProvider = Field(default="openai", description="LLM provider to use")

    # OpenAI Configuration
    openai_api_key: str = Field(default="sk-test-openai-dummy-key", description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL"
    )

    # Anthropic Configuration (future)
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")

    # Azure OpenAI Configuration (future)
    azure_api_key: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    azure_endpoint: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")

    # Google Vertex AI Configuration (future)
    google_project_id: Optional[str] = Field(default=None, description="Google Cloud project ID")
    google_credentials_path: Optional[str] = Field(
        default=None, description="Path to Google Cloud credentials JSON"
    )

    # Default Model Configuration (provider-agnostic)
    default_model: str = Field(default="gpt-4o-mini", description="Default LLM model to use")
    default_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Default temperature for LLM responses"
    )
    default_max_tokens: int = Field(
        default=2000, gt=0, description="Default maximum tokens for LLM responses"
    )

    # Summarization Settings (LangMem)
    # Controls when and how conversation history is summarized for long sessions
    summarization_max_tokens: int = Field(
        default=256,
        gt=0,
        description="Max tokens to return to LLM after summarization (context window for LLM)",
    )
    summarization_trigger_tokens: int = Field(
        default=1024,
        gt=0,
        description="Token threshold that triggers summarization (conversation length before summary)",
    )
    summarization_summary_tokens: int = Field(
        default=128, gt=0, description="Max tokens for the summary itself"
    )

    # Rate limiting and timeouts
    request_timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(
        default=3, ge=0, description="Maximum number of retries for failed requests"
    )


# Global instance
llm_settings = LLMSettings()
