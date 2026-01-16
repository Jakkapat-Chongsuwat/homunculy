"""HTTP RAG Service Client."""

from typing import Any, Dict, List

import httpx

from internal.domain.services import RAGService


class HTTPRAGService(RAGService):
    """HTTP client for RAG service."""

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: float = 30.0,
    ) -> None:
        """Initialize HTTP RAG client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Retrieve documents via HTTP."""
        url = f"{self.base_url}/api/v1/query"
        payload = {
            "query": query,
            "top_k": top_k,
            "namespace": namespace,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return self.parse_results(data)

    async def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Web search fallback (placeholder)."""
        # TODO: Implement actual web search via Tavily or similar
        return []

    def parse_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse API response to documents."""
        results = data.get("results", [])
        return [
            {
                "id": r.get("id", ""),
                "content": r.get("text", "") or r.get("content", ""),
                "score": r.get("score", 0.0),
                "metadata": r.get("metadata"),
            }
            for r in results
        ]
