"""
Chunking Service Interface.

Abstract interface for document text splitting.
"""

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
)

from internal.domain.entities import (
    Document,
    DocumentChunk,
)


class ChunkingService(ABC):
    """
    Abstract interface for document chunking.

    Implementations: LangChainChunkingService
    """

    @abstractmethod
    def chunk_document(
        self,
        document: Document,
    ) -> List[DocumentChunk]:
        """
        Split document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of document chunks
        """

    @abstractmethod
    def chunk_text(
        self,
        text: str,
        document_id: str,
        source: str,
    ) -> List[DocumentChunk]:
        """
        Split text into chunks.

        Args:
            text: Text content to chunk
            document_id: Parent document ID
            source: Source identifier

        Returns:
            List of document chunks
        """

    @property
    @abstractmethod
    def chunk_size(
        self,
    ) -> int:
        """Get chunk size in tokens."""

    @property
    @abstractmethod
    def chunk_overlap(
        self,
    ) -> int:
        """Get chunk overlap in tokens."""
