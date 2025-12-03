"""RAG Service Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class RAGService(ABC):
    """Abstract interface for RAG operations."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""

    @abstractmethod
    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search web for additional context."""
