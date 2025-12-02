"""
Embedding service settings.

Configuration for OpenAI embeddings.
"""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    """
    Embedding configuration settings.

    Environment Variables:
        OPENAI_API_KEY: OpenAI API key for embeddings
        EMBEDDING_MODEL: Model name (text-embedding-3-small recommended)
        EMBEDDING_DIMENSION: Vector dimension (1536 for text-embedding-3-small)
        EMBEDDING_BATCH_SIZE: Batch size for embedding requests
    """

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", extra="ignore")

    openai_api_key: str = os.getenv(
        "OPENAI_API_KEY",
        "",
    )
    model: str = os.getenv(
        "EMBEDDING_MODEL",
        "text-embedding-3-small",
    )
    dimension: int = int(
        os.getenv(
            "EMBEDDING_DIMENSION",
            "1536",
        )
    )
    batch_size: int = int(
        os.getenv(
            "EMBEDDING_BATCH_SIZE",
            "100",
        )
    )


embedding_settings = EmbeddingSettings()
