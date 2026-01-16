"""RAG service contract."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RAGService(ABC):
    """RAG operations contract."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents."""

    @abstractmethod
    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search the web for context."""
