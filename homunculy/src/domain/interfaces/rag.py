"""RAG service port (interface)."""

from abc import ABC, abstractmethod
from typing import Any


class RAGPort(ABC):
    """RAG (Retrieval Augmented Generation) contract."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents for query."""
        ...

    @abstractmethod
    async def ingest(
        self,
        documents: list[dict[str, Any]],
    ) -> int:
        """Ingest documents into vector store. Returns count."""
        ...
