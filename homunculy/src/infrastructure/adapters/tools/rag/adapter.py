"""RAG Tool Adapter - Wraps RAG graph as an agent tool.

This adapter exposes the RAG workflow as a tool that can be
called by the supervisor's sub-agents (e.g., researcher agent).

Clean Architecture:
- Domain: ToolPort interface (if needed)
- Application: RAG graph builder defines WHAT nodes do
- Infrastructure: This adapter wires it to LangGraph + exposes as tool
"""

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from common.logger import get_logger

logger = get_logger(__name__)


class RAGGraphPort(Protocol):
    """Protocol for RAG graph execution."""

    async def invoke(self, query: str) -> dict[str, Any]:
        """Execute RAG query and return result."""
        ...


@dataclass
class RAGToolConfig:
    """Configuration for RAG tool."""

    max_documents: int = 5
    include_sources: bool = True
    max_retries: int = 3


@dataclass
class RAGToolResult:
    """Result from RAG tool execution."""

    answer: str
    sources: list[dict[str, Any]]
    documents_used: int


class RAGToolAdapter:
    """Wraps RAG graph as an invokable tool."""

    def __init__(
        self,
        rag_graph: RAGGraphPort,
        config: RAGToolConfig | None = None,
    ) -> None:
        self._graph = rag_graph
        self._config = config or RAGToolConfig()

    async def execute(self, query: str) -> RAGToolResult:
        """Execute RAG query."""
        logger.info("RAG tool executing", query=query[:50])
        result = await self._graph.invoke(query)
        return self._parse_result(result)

    def _parse_result(self, result: dict[str, Any]) -> RAGToolResult:
        """Parse graph result into tool result."""
        return RAGToolResult(
            answer=result.get("generation", ""),
            sources=self._extract_sources(result),
            documents_used=len(result.get("documents", [])),
        )

    def _extract_sources(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract source references from documents."""
        if not self._config.include_sources:
            return []
        docs = result.get("documents", [])
        return [
            {"content": d.get("content", "")[:200], "metadata": d.get("metadata", {})} for d in docs
        ]

    def as_tool_spec(self) -> dict[str, Any]:
        """Return OpenAI-compatible tool specification."""
        return {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    def as_langchain_tool(self) -> Callable:
        """Return as a LangChain-compatible tool function."""

        async def _tool(query: str) -> str:
            result = await self.execute(query)
            return result.answer

        _tool.__name__ = "search_knowledge_base"
        _tool.__doc__ = "Search the knowledge base for relevant information"
        return _tool
