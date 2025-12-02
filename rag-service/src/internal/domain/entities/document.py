"""
Document entities for RAG system.

Represents documents and their chunks for vector storage.
"""

from dataclasses import (
    dataclass,
    field,
)
from datetime import (
    datetime,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)
from uuid import (
    uuid4,
)


@dataclass
class DocumentMetadata:
    """
    Metadata associated with a document.

    Attributes:
        source: Original source (filename, URL, etc.)
        title: Document title
        category: Category for filtering
        created_at: Creation timestamp
        custom: Additional custom metadata
    """

    source: str
    title: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    custom: Dict[
        str,
        Any,
    ] = field(default_factory=dict)

    def to_dict(
        self,
    ) -> Dict[str, Any,]:
        """Convert to dictionary for storage."""
        return {
            "source": self.source,
            "title": self.title or "",
            "category": self.category or "",
            "created_at": self.created_at.isoformat(),
            **self.custom,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[
            str,
            Any,
        ],
    ) -> "DocumentMetadata":
        """Create from dictionary."""
        return cls(
            source=data.get(
                "source",
                "unknown",
            ),
            title=data.get("title"),
            category=data.get("category"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.utcnow()
            ),
            custom={
                k: v
                for k, v in data.items()
                if k
                not in [
                    "source",
                    "title",
                    "category",
                    "created_at",
                ]
            },
        )


@dataclass
class DocumentChunk:
    """
    A chunk of a document with its embedding.

    Attributes:
        id: Unique chunk identifier
        document_id: Parent document ID
        text: Chunk text content
        embedding: Vector embedding (1536 dimensions for text-embedding-3-small)
        chunk_index: Position in original document
        metadata: Associated metadata
    """

    id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: DocumentMetadata
    embedding: Optional[List[float]] = None

    @classmethod
    def create(
        cls,
        document_id: str,
        text: str,
        chunk_index: int,
        metadata: DocumentMetadata,
        embedding: Optional[List[float]] = None,
    ) -> "DocumentChunk":
        """Factory method to create a chunk with generated ID."""
        chunk_id = f"{document_id}_chunk_{chunk_index}"
        return cls(
            id=chunk_id,
            document_id=document_id,
            text=text,
            chunk_index=chunk_index,
            metadata=metadata,
            embedding=embedding,
        )

    def to_vector_record(
        self,
    ) -> Dict[str, Any,]:
        """
        Convert to Pinecone vector record format.

        Returns:
            Dict with id, values (embedding), and metadata
        """
        if self.embedding is None:
            raise ValueError("Embedding must be set before converting to vector record")

        return {
            "id": self.id,
            "values": self.embedding,
            "metadata": {
                "document_id": self.document_id,
                "text": self.text,
                "chunk_index": self.chunk_index,
                **self.metadata.to_dict(),
            },
        }


@dataclass
class Document:
    """
    A document to be indexed for RAG.

    Attributes:
        id: Unique document identifier
        content: Full document text
        metadata: Document metadata
        chunks: List of document chunks (after splitting)
    """

    id: str
    content: str
    metadata: DocumentMetadata
    chunks: List[DocumentChunk] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        content: str,
        source: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        custom_metadata: Optional[
            Dict[
                str,
                Any,
            ]
        ] = None,
    ) -> "Document":
        """Factory method to create a document with generated ID."""
        doc_id = str(uuid4())
        metadata = DocumentMetadata(
            source=source,
            title=title,
            category=category,
            custom=custom_metadata or {},
        )
        return cls(
            id=doc_id,
            content=content,
            metadata=metadata,
        )

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
    ) -> None:
        """Add chunks to the document."""
        self.chunks = chunks

    @property
    def chunk_count(
        self,
    ) -> int:
        """Get number of chunks."""
        return len(self.chunks)
