"""
Pinecone vector database settings.

Supports both Pinecone Cloud and Pinecone Local for development.
"""

import os
from enum import (
    Enum,
)
from typing import (
    Optional,
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class PineconeEnvironment(
    str,
    Enum,
):
    """Pinecone environment options."""

    CLOUD = "cloud"
    LOCAL = "local"


class PineconeSettings(BaseSettings):
    """
    Pinecone configuration settings.

    Environment Variables:
        PINECONE_API_KEY: API key (any value for local)
        PINECONE_ENVIRONMENT: 'cloud' or 'local'
        PINECONE_HOST: Host URL for Pinecone Local
        PINECONE_INDEX_NAME: Name of the index
        PINECONE_DIMENSION: Vector dimension (1536 for text-embedding-3-small)
        PINECONE_METRIC: Distance metric (cosine, euclidean, dotproduct)
        PINECONE_NAMESPACE: Default namespace
    """

    model_config = SettingsConfigDict(env_prefix="PINECONE_", extra="ignore")

    api_key: str = os.getenv(
        "PINECONE_API_KEY",
        "pclocal",
    )
    environment: PineconeEnvironment = PineconeEnvironment(
        os.getenv(
            "PINECONE_ENVIRONMENT",
            "local",
        )
    )
    host: Optional[str] = os.getenv("PINECONE_HOST")
    index_name: str = os.getenv(
        "PINECONE_INDEX_NAME",
        "homunculy-rag",
    )
    dimension: int = int(
        os.getenv(
            "PINECONE_DIMENSION",
            "1536",
        )
    )
    metric: str = os.getenv(
        "PINECONE_METRIC",
        "cosine",
    )
    namespace: str = os.getenv(
        "PINECONE_NAMESPACE",
        "default",
    )

    @property
    def is_local(
        self,
    ) -> bool:
        """Check if using Pinecone Local."""
        return self.environment == PineconeEnvironment.LOCAL

    @property
    def effective_host(
        self,
    ) -> str:
        """Get effective host URL."""
        if self.is_local:
            return self.host or "localhost:5081"
        return self.host or ""

    @property
    def use_grpc(
        self,
    ) -> bool:
        """Use gRPC for better performance."""
        return True

    @property
    def secure(
        self,
    ) -> bool:
        """Use TLS. Disabled for local development."""
        return not self.is_local


pinecone_settings = PineconeSettings()
