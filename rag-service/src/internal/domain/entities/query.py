"""
Query entities for RAG retrieval.

Represents search queries and results.
"""

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)


@dataclass
class QueryRequest:
    """
    A query request for semantic search.

    Attributes:
        query: Natural language query text
        top_k: Number of results to return
        filter: Metadata filter (e.g., {"category": "docs"})
        namespace: Pinecone namespace to search
        include_metadata: Whether to include metadata in results
        similarity_threshold: Minimum similarity score (0-1)
    """

    query: str
    top_k: int = 5
    filter: Optional[
        Dict[
            str,
            Any,
        ]
    ] = None
    namespace: str = "default"
    include_metadata: bool = True
    similarity_threshold: float = 0.0


@dataclass
class QueryResult:
    """
    A single search result.

    Attributes:
        id: Vector ID (chunk ID)
        text: Retrieved text content
        score: Similarity score (0-1)
        metadata: Associated metadata
    """

    id: str
    text: str
    score: float
    metadata: Dict[
        str,
        Any,
    ] = field(default_factory=dict)

    @classmethod
    def from_pinecone_match(
        cls,
        match: Any,
    ) -> "QueryResult":
        """Create from Pinecone match result (supports both dict and object)."""
        # Handle both dict and object formats (REST vs GRPC client)
        if isinstance(match, dict):
            metadata = match.get("metadata", {})
            return cls(
                id=match["id"],
                text=metadata.get("text", ""),
                score=match.get("score", 0.0),
                metadata=metadata,
            )
        else:
            # GRPC protobuf object format - access attributes directly
            match_id = match.id if hasattr(match, "id") else ""
            score = match.score if hasattr(match, "score") else 0.0
            # metadata is a dict-like object in protobuf
            raw_metadata = match.metadata if hasattr(match, "metadata") else {}
            metadata = dict(raw_metadata) if raw_metadata else {}
            return cls(
                id=match_id,
                text=metadata.get("text", ""),
                score=score,
                metadata=metadata,
            )


@dataclass
class QueryResponse:
    """
    Response containing search results.

    Attributes:
        results: List of search results
        query: Original query text
        total_results: Number of results returned
        namespace: Namespace searched
    """

    results: List[QueryResult]
    query: str
    total_results: int
    namespace: str = "default"

    def to_dict(
        self,
    ) -> Dict[
        str,
        Any,
    ]:
        """Convert to dictionary for API response."""
        return {
            "results": [
                {
                    "id": r.id,
                    "text": r.text,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
            "query": self.query,
            "total_results": self.total_results,
            "namespace": self.namespace,
        }

    def get_context_text(
        self,
        separator: str = "\n\n",
    ) -> str:
        """
        Get combined text from all results for LLM context.

        Args:
            separator: Text separator between chunks

        Returns:
            Combined text from all results
        """
        return separator.join(r.text for r in self.results if r.text)
