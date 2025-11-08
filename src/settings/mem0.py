"""
Mem0 Configuration Settings.

Mem0 provides intelligent memory layer for AI agents with short-term 
and long-term memory capabilities.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mem0Settings(BaseSettings):
    """Mem0 configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_prefix='MEM0_',
        extra='ignore',
    )
    
    # API Configuration
    api_key: Optional[str] = Field(
        default=None,
        description="Mem0 Platform API key for hosted service. Leave None for self-hosted.",
    )
    
    # LLM Configuration
    llm_provider: str = Field(
        default="openai",
        description="LLM provider for memory inference (openai, anthropic, etc.)",
    )
    
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model to use for memory operations",
    )
    
    llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for LLM provider. Falls back to OPENAI_API_KEY env var.",
    )
    
    # Vector Store Configuration (for self-hosted)
    vector_store_provider: str = Field(
        default="qdrant",
        description="Vector store provider (qdrant, chromadb, pgvector, etc.)",
    )
    
    vector_store_host: str = Field(
        default="localhost",
        description="Vector store host",
    )
    
    vector_store_port: int = Field(
        default=6333,
        description="Vector store port",
    )
    
    # Memory Behavior
    enable_infer: bool = Field(
        default=True,
        description="Enable automatic memory inference from conversations",
    )
    
    search_limit: int = Field(
        default=5,
        description="Default number of memories to retrieve in search",
    )
    
    def __init__(self, **kwargs):
        """Initialize Mem0 settings with environment variable fallbacks."""
        super().__init__(**kwargs)
        
        # Fallback to OPENAI_API_KEY if llm_api_key not set
        if not self.llm_api_key and self.llm_provider == "openai":
            self.llm_api_key = os.getenv("OPENAI_API_KEY")
    
    def get_config(self) -> dict:
        """
        Get Mem0 configuration dict for initialization.
        
        Returns:
            Configuration dict for Memory() initialization
        """
        # If using hosted platform
        if self.api_key:
            return {"api_key": self.api_key}
        
        # Self-hosted configuration
        config = {
            "llm": {
                "provider": self.llm_provider,
                "config": {
                    "model": self.llm_model,
                    "temperature": 0.7,
                }
            }
        }
        
        # Add LLM API key if available
        if self.llm_api_key:
            config["llm"]["config"]["api_key"] = self.llm_api_key
        
        # Add vector store configuration
        if self.vector_store_provider == "qdrant":
            config["vector_store"] = {
                "provider": "qdrant",
                "config": {
                    "host": self.vector_store_host,
                    "port": self.vector_store_port,
                }
            }
        
        return config


# Global settings instance
mem0_settings = Mem0Settings()
