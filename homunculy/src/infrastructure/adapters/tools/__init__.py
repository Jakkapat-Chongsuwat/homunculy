"""RAG Tool - Retrieval Augmented Generation as a tool.

This wraps the RAG workflow graph as a tool that can be
invoked by sub-agents (e.g., researcher agent).
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class RAGToolInput:
    """Input for RAG tool."""

    query: str
    max_documents: int = 5
    include_sources: bool = True


@dataclass
class RAGToolOutput:
    """Output from RAG tool."""

    answer: str
    sources: list[dict[str, Any]] | None = None
    confidence: float = 0.0
