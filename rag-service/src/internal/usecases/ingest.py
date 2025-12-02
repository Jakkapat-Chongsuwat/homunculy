"""
Document Ingestion Use Case.

Handles the data pipeline: chunking → embedding → vector storage.
"""

from dataclasses import (
    dataclass,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from internal.domain.entities import (
    Document,
)
from internal.domain.services import (
    ChunkingService,
    EmbeddingService,
    VectorStoreService,
)
from settings.logging import (
    get_logger,
)

logger = get_logger(__name__)


@dataclass
class IngestResult:
    """Result of document ingestion."""

    document_id: str
    chunk_count: int
    vectors_upserted: int
    source: str
    success: bool
    error: Optional[str] = None

    def to_dict(
        self,
    ) -> Dict[str, Any,]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "chunk_count": self.chunk_count,
            "vectors_upserted": self.vectors_upserted,
            "source": self.source,
            "success": self.success,
            "error": self.error,
        }


class IngestUseCase:
    """
    Document ingestion use case.

    Pipeline:
    1. Chunk document into smaller pieces
    2. Generate embeddings for each chunk
    3. Upsert vectors to Pinecone
    """

    def __init__(
        self,
        vector_store: VectorStoreService,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            vector_store: Vector store service
            embedding_service: Embedding service
            chunking_service: Chunking service
        """
        self._vector_store = vector_store
        self._embedding_service = embedding_service
        self._chunking_service = chunking_service

    async def ingest_text(
        self,
        text: str,
        source: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        namespace: str = "default",
        custom_metadata: Optional[
            Dict[
                str,
                Any,
            ]
        ] = None,
    ) -> IngestResult:
        """
        Ingest text content into vector store.

        Args:
            text: Text content to ingest
            source: Source identifier
            title: Optional document title
            category: Optional category for filtering
            namespace: Pinecone namespace
            custom_metadata: Additional metadata

        Returns:
            IngestResult with ingestion details
        """
        logger.info(
            "Starting text ingestion",
            source=source,
            text_length=len(text),
            namespace=namespace,
        )

        try:
            # Create document
            document = Document.create(
                content=text,
                source=source,
                title=title,
                category=category,
                custom_metadata=custom_metadata,
            )

            # Chunk document
            chunks = self._chunking_service.chunk_document(document)
            document.add_chunks(chunks)

            logger.info(
                "Document chunked",
                document_id=document.id,
                chunk_count=len(chunks),
            )

            # Generate embeddings for all chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await self._embedding_service.embed_batch(chunk_texts)

            # Attach embeddings to chunks
            for (
                chunk,
                embedding,
            ) in zip(
                chunks,
                embeddings,
            ):
                chunk.embedding = embedding

            logger.info(
                "Embeddings generated",
                document_id=document.id,
                embedding_count=len(embeddings),
            )

            # Upsert to vector store
            vectors_upserted = await self._vector_store.upsert(
                chunks=chunks,
                namespace=namespace,
            )

            logger.info(
                "Ingestion complete",
                document_id=document.id,
                vectors_upserted=vectors_upserted,
            )

            return IngestResult(
                document_id=document.id,
                chunk_count=len(chunks),
                vectors_upserted=vectors_upserted,
                source=source,
                success=True,
            )

        except Exception as e:
            logger.error(
                "Ingestion failed",
                source=source,
                error=str(e),
                exc_info=True,
            )
            return IngestResult(
                document_id="",
                chunk_count=0,
                vectors_upserted=0,
                source=source,
                success=False,
                error=str(e),
            )

    async def ingest_document(
        self,
        document: Document,
        namespace: str = "default",
    ) -> IngestResult:
        """
        Ingest a pre-created document.

        Args:
            document: Document to ingest
            namespace: Pinecone namespace

        Returns:
            IngestResult with ingestion details
        """
        return await self.ingest_text(
            text=document.content,
            source=document.metadata.source,
            title=document.metadata.title,
            category=document.metadata.category,
            namespace=namespace,
            custom_metadata=document.metadata.custom,
        )

    async def ingest_batch(
        self,
        documents: List[Document],
        namespace: str = "default",
    ) -> List[IngestResult]:
        """
        Ingest multiple documents.

        Args:
            documents: List of documents to ingest
            namespace: Pinecone namespace

        Returns:
            List of IngestResult for each document
        """
        results = []
        for document in documents:
            result = await self.ingest_document(
                document,
                namespace,
            )
            results.append(result)
        return results
