"""
Document Retrieval Use Case.

Handles semantic search: query → embedding → vector search → results.
"""

from typing import (
    Any,
    Dict,
    Optional,
)

from internal.domain.entities import (
    QueryRequest,
    QueryResponse,
)
from internal.domain.services import (
    EmbeddingService,
    VectorStoreService,
)
from settings import (
    rag_settings,
)
from settings.logging import (
    get_logger,
)

logger = get_logger(__name__)


class RetrieveUseCase:
    """
    Document retrieval use case.

    Pipeline:
    1. Generate embedding for query
    2. Search vector store
    3. Return ranked results
    """

    def __init__(
        self,
        vector_store: VectorStoreService,
        embedding_service: EmbeddingService,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            vector_store: Vector store service
            embedding_service: Embedding service
        """
        self._vector_store = vector_store
        self._embedding_service = embedding_service

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[
            Dict[
                str,
                Any,
            ]
        ] = None,
        namespace: str = "default",
        similarity_threshold: Optional[float] = None,
    ) -> QueryResponse:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Natural language query
            top_k: Number of results (default from settings)
            metadata_filter: Metadata filter for results
            namespace: Pinecone namespace
            similarity_threshold: Minimum similarity score

        Returns:
            QueryResponse with ranked results
        """
        logger.info(
            "Starting retrieval",
            query_preview=query[:50],
            top_k=top_k or rag_settings.top_k,
            namespace=namespace,
        )

        # Generate query embedding
        query_embedding = await self._embedding_service.embed_text(query)

        logger.debug(
            "Query embedding generated",
            embedding_dimension=len(query_embedding),
        )

        # Build query request
        request = QueryRequest(
            query=query,
            top_k=top_k or rag_settings.top_k,
            filter=metadata_filter,
            namespace=namespace,
            similarity_threshold=similarity_threshold or rag_settings.similarity_threshold,
        )

        # Search vector store
        response = await self._vector_store.query(
            embedding=query_embedding,
            request=request,
        )

        logger.info(
            "Retrieval complete",
            query=query[:50],
            results_count=response.total_results,
        )

        return response

    async def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[
            Dict[
                str,
                Any,
            ]
        ] = None,
        namespace: str = "default",
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Retrieve and combine context for LLM.

        Convenience method that returns combined text from results,
        ready to be injected into an LLM prompt.

        Args:
            query: Natural language query
            top_k: Number of results
            metadata_filter: Metadata filter for results
            namespace: Pinecone namespace
            separator: Text separator between chunks

        Returns:
            Combined context text
        """
        response = await self.retrieve(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            namespace=namespace,
        )

        return response.get_context_text(separator=separator)
