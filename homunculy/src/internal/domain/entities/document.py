"""RAG Document Entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Document:
    """Represents a retrieved document."""

    id: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create Document from dictionary."""
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            score=data.get("score", 0.0),
            metadata=data.get("metadata"),
        )

    def is_relevant(self, threshold: float = 0.7) -> bool:
        """Check if document score meets relevance threshold."""
        return self.score >= threshold
