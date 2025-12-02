"""
LangChain Chunking Service Implementation.

Splits documents into chunks using LangChain text splitters.
"""

from typing import (
    List,
    Optional,
)
from uuid import (
    uuid4,
)

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from internal.domain.entities import (
    Document,
    DocumentChunk,
    DocumentMetadata,
)
from internal.domain.services import (
    ChunkingService,
)
from settings import (
    rag_settings,
)
from settings.logging import (
    get_logger,
)

logger = get_logger(__name__)


class LangChainChunkingService(ChunkingService):
    """
    LangChain-based text chunking service.

    Uses RecursiveCharacterTextSplitter for intelligent chunking
    that respects document structure (paragraphs, sentences).
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> None:
        """
        Initialize chunking service.

        Args:
            chunk_size: Target chunk size in characters (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
        """
        self._chunk_size = chunk_size or rag_settings.chunk_size
        self._chunk_overlap = chunk_overlap or rag_settings.chunk_overlap

        # Initialize text splitter
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

        logger.info(
            "Chunking service initialized",
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

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
        return self.chunk_text(
            text=document.content,
            document_id=document.id,
            source=document.metadata.source,
            metadata=document.metadata,
        )

    def chunk_text(
        self,
        text: str,
        document_id: Optional[str] = None,
        source: str = "unknown",
        metadata: Optional[DocumentMetadata] = None,
    ) -> List[DocumentChunk]:
        """
        Split text into chunks.

        Args:
            text: Text content to chunk
            document_id: Parent document ID (auto-generated if None)
            source: Source identifier
            metadata: Optional metadata to attach

        Returns:
            List of document chunks
        """
        if not document_id:
            document_id = str(uuid4())

        if not metadata:
            metadata = DocumentMetadata(source=source)

        # Split text
        text_chunks = self._splitter.split_text(text)

        logger.info(
            "Text chunked",
            document_id=document_id,
            original_length=len(text),
            chunk_count=len(text_chunks),
        )

        # Create DocumentChunk objects
        chunks = []
        for (
            i,
            chunk_text,
        ) in enumerate(text_chunks):
            chunk = DocumentChunk.create(
                document_id=document_id,
                text=chunk_text,
                chunk_index=i,
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    @property
    def chunk_size(
        self,
    ) -> int:
        """Get chunk size."""
        return self._chunk_size

    @property
    def chunk_overlap(
        self,
    ) -> int:
        """Get chunk overlap."""
        return self._chunk_overlap
