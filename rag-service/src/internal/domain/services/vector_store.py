"""
Vector Store Service Interface.

Abstract interface for vector database operations.
"""

from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from internal.domain.entities import (
    DocumentChunk,
    QueryRequest,
    QueryResponse,
)


class VectorStoreService(ABC):
    """
    Abstract interface for vector store operations.

    Implementations: PineconeVectorStore
    """

    @abstractmethod
    async def upsert(
        self,
        chunks: List[DocumentChunk],
        namespace: str = "default",
    ) -> int:
        """
        Upsert document chunks to vector store.

        Args:
            chunks: List of chunks with embeddings
            namespace: Target namespace

        Returns:
            Number of vectors upserted
        """

    @abstractmethod
    async def query(
        self,
        embedding: List[float],
        request: QueryRequest,
    ) -> QueryResponse:
        """
        Query vector store for similar documents.

        Args:
            embedding: Query vector embedding
            request: Query parameters

        Returns:
            Query response with results
        """

    @abstractmethod
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        metadata_filter: Optional[
            Dict[
                str,
                Any,
            ]
        ] = None,
        namespace: str = "default",
        delete_all: bool = False,
    ) -> int:
        """
        Delete vectors from store.

        Args:
            ids: Specific vector IDs to delete
            metadata_filter: Metadata filter for deletion
            namespace: Target namespace
            delete_all: Delete all vectors in namespace

        Returns:
            Number of vectors deleted
        """

    @abstractmethod
    async def get_index_stats(
        self,
    ) -> Dict[str, Any,]:
        """
        Get index statistics.

        Returns:
            Dict with index stats (vector count, dimension, etc.)
        """
