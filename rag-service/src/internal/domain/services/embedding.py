"""
Embedding Service Interface.

Abstract interface for text embedding generation.
"""

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
)


class EmbeddingService(ABC):
    """
    Abstract interface for embedding generation.

    Implementations: OpenAIEmbeddingService
    """

    @abstractmethod
    async def embed_text(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """

    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """

    @property
    @abstractmethod
    def dimension(
        self,
    ) -> int:
        """Get embedding dimension."""

    @property
    @abstractmethod
    def model_name(
        self,
    ) -> str:
        """Get model name."""
