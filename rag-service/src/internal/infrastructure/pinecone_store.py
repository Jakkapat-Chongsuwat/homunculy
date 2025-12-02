"""
Pinecone Vector Store Implementation.

Supports both Pinecone Cloud and Pinecone Local (Docker).
"""

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
    QueryResult,
)
from internal.domain.services import (
    VectorStoreService,
)
from settings import (
    pinecone_settings,
)
from settings.logging import (
    get_logger,
)

logger = get_logger(__name__)


class PineconeVectorStore(VectorStoreService):
    """
    Pinecone vector store implementation.

    Supports:
    - Pinecone Cloud (production)
    - Pinecone Local (development via Docker)
    """

    def __init__(
        self,
    ) -> None:
        """Initialize Pinecone client."""
        self._index = None
        self._initialize_client()

    def _initialize_client(
        self,
    ) -> None:
        """Initialize Pinecone client based on environment."""
        from pinecone.grpc import (
            GRPCClientConfig,
            PineconeGRPC,
        )

        if pinecone_settings.is_local:
            logger.info(
                "Connecting to Pinecone Local",
                host=pinecone_settings.effective_host,
            )
            # Pinecone Local - connect directly to index
            pc = PineconeGRPC(api_key=pinecone_settings.api_key)
            self._index = pc.Index(
                host=pinecone_settings.effective_host,
                grpc_config=GRPCClientConfig(secure=False),
            )
        else:
            logger.info(
                "Connecting to Pinecone Cloud",
                index=pinecone_settings.index_name,
            )
            # Pinecone Cloud
            pc = PineconeGRPC(api_key=pinecone_settings.api_key)
            self._index = pc.Index(pinecone_settings.index_name)

        logger.info("Pinecone client initialized")

    async def upsert(
        self,
        chunks: List[DocumentChunk],
        namespace: str = "default",
    ) -> int:
        """
        Upsert document chunks to Pinecone.

        Args:
            chunks: Chunks with embeddings to upsert
            namespace: Target namespace

        Returns:
            Number of vectors upserted
        """
        if not chunks:
            return 0

        vectors = [chunk.to_vector_record() for chunk in chunks]

        logger.info(
            "Upserting vectors to Pinecone",
            count=len(vectors),
            namespace=namespace,
        )

        # Batch upsert for efficiency
        batch_size = 100
        total_upserted = 0

        for i in range(
            0,
            len(vectors),
            batch_size,
        ):
            batch = vectors[i : i + batch_size]
            self._index.upsert(
                vectors=batch,
                namespace=namespace,
            )
            total_upserted += len(batch)

            logger.debug(
                "Upserted batch",
                batch_start=i,
                batch_size=len(batch),
            )

        logger.info(
            "Upsert complete",
            total_upserted=total_upserted,
        )
        return total_upserted

    async def query(
        self,
        embedding: List[float],
        request: QueryRequest,
    ) -> QueryResponse:
        """
        Query Pinecone for similar vectors.

        Args:
            embedding: Query vector
            request: Query parameters

        Returns:
            Query response with results
        """
        logger.info(
            "Querying Pinecone",
            top_k=request.top_k,
            namespace=request.namespace,
            has_filter=request.filter is not None,
        )

        query_response = self._index.query(
            vector=embedding,
            top_k=request.top_k,
            namespace=request.namespace,
            filter=request.filter,
            include_values=False,
            include_metadata=request.include_metadata,
        )

        # Convert matches to QueryResult
        results = []
        for match in query_response.get(
            "matches",
            [],
        ):
            # Apply similarity threshold
            score = match.get(
                "score",
                0.0,
            )
            if score >= request.similarity_threshold:
                results.append(QueryResult.from_pinecone_match(match))

        logger.info(
            "Query complete",
            total_matches=len(
                query_response.get(
                    "matches",
                    [],
                )
            ),
            filtered_results=len(results),
        )

        return QueryResponse(
            results=results,
            query=request.query,
            total_results=len(results),
            namespace=request.namespace,
        )

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
        Delete vectors from Pinecone.

        Args:
            ids: Specific vector IDs to delete
            metadata_filter: Metadata filter for deletion
            namespace: Target namespace
            delete_all: Delete all vectors in namespace

        Returns:
            Number of vectors deleted (estimated)
        """
        logger.info(
            "Deleting vectors from Pinecone",
            namespace=namespace,
            delete_all=delete_all,
            id_count=(len(ids) if ids else 0),
        )

        if delete_all:
            self._index.delete(
                delete_all=True,
                namespace=namespace,
            )
            return -1  # Unknown count for delete_all
        elif ids:
            self._index.delete(
                ids=ids,
                namespace=namespace,
            )
            return len(ids)
        elif metadata_filter:
            self._index.delete(
                filter=metadata_filter,
                namespace=namespace,
            )
            return -1  # Unknown count for filter delete

        return 0

    async def get_index_stats(
        self,
    ) -> Dict[str, Any,]:
        """
        Get Pinecone index statistics.

        Returns:
            Dict with index stats
        """
        stats = self._index.describe_index_stats()

        return {
            "index_name": pinecone_settings.index_name,
            "dimension": stats.get("dimension"),
            "total_vector_count": stats.get(
                "total_vector_count",
                0,
            ),
            "namespaces": stats.get(
                "namespaces",
                {},
            ),
            "index_fullness": stats.get(
                "index_fullness",
                0,
            ),
        }
