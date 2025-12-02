"""
Dependency Injection Container.

Provides service instances for the application using singleton pattern.
"""

from typing import (
    Optional,
)

from internal.domain.services import (
    ChunkingService,
    EmbeddingService,
    VectorStoreService,
)
from internal.infrastructure.chunking import (
    LangChainChunkingService,
)
from internal.infrastructure.openai_embeddings import (
    OpenAIEmbeddingService,
)
from internal.infrastructure.pinecone_store import (
    PineconeVectorStore,
)


class ServiceContainer:
    """
    Service container for dependency injection.

    Manages singleton instances of services.
    """

    _vector_store: Optional[VectorStoreService] = None
    _embedding_service: Optional[EmbeddingService] = None
    _chunking_service: Optional[ChunkingService] = None

    @classmethod
    def get_vector_store(cls) -> VectorStoreService:
        """Get vector store service instance (singleton)."""
        if cls._vector_store is None:
            cls._vector_store = PineconeVectorStore()
        return cls._vector_store

    @classmethod
    def get_embedding_service(cls) -> EmbeddingService:
        """Get embedding service instance (singleton)."""
        if cls._embedding_service is None:
            cls._embedding_service = OpenAIEmbeddingService()
        return cls._embedding_service

    @classmethod
    def get_chunking_service(cls) -> ChunkingService:
        """Get chunking service instance (singleton)."""
        if cls._chunking_service is None:
            cls._chunking_service = LangChainChunkingService()
        return cls._chunking_service

    @classmethod
    def reset(cls) -> None:
        """Reset all service instances (useful for testing)."""
        cls._vector_store = None
        cls._embedding_service = None
        cls._chunking_service = None


# Convenience functions for backward compatibility
def get_vector_store_service() -> VectorStoreService:
    """Get vector store service instance."""
    return ServiceContainer.get_vector_store()


def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    return ServiceContainer.get_embedding_service()


def get_chunking_service() -> ChunkingService:
    """Get chunking service instance."""
    return ServiceContainer.get_chunking_service()
