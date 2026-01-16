"""
RAG Search Tool for LangGraph Agents.

Provides document retrieval capability to agents through tool calling interface.
Uses the self-reflective RAG system for high-quality document search.
"""

from typing import Annotated

from common.logger import get_logger
from langchain_core.tools import tool

from internal.domain.services import RAGService

logger = get_logger(__name__)


def create_rag_search_tool(rag_service: RAGService):
    """
    Create a RAG search tool for LangGraph agents.

    This factory function creates a tool with the RAG service injected,
    allowing the agent to search documents for relevant context.

    Args:
        rag_service: RAG service implementation (injected via DI)

    Returns:
        LangChain tool that can be registered with agents
    """

    @tool
    async def search_documents(
        query: Annotated[str, "The search query to find relevant documents"],
        top_k: Annotated[int, "Number of documents to retrieve"] = 5,
    ) -> str:
        """
        Search for relevant documents in the knowledge base.

        Use this tool when you need to find information from documents,
        answer questions that require specific knowledge, or verify facts.
        Returns relevant document excerpts that can be used to answer questions.
        """
        try:
            logger.info(
                "Agent invoking RAG search tool",
                query=query[:100],
                top_k=top_k,
            )

            documents = await rag_service.retrieve(query, top_k=top_k)

            if not documents:
                logger.info("No documents found", query=query[:50])
                return "No relevant documents found for this query."

            # Format results for agent consumption
            results = []
            for i, doc in enumerate(documents, 1):
                content = doc.get("content", "")
                score = doc.get("score", 0.0)
                source = (
                    doc.get("metadata", {}).get("source", "unknown")
                    if doc.get("metadata")
                    else "unknown"
                )
                results.append(f"[{i}] (score: {score:.2f}, source: {source})\n{content}")

            formatted = "\n\n---\n\n".join(results)
            logger.info(
                "RAG search completed",
                query=query[:50],
                results_count=len(documents),
            )
            return f"Found {len(documents)} relevant documents:\n\n{formatted}"

        except Exception as e:
            logger.error("RAG search tool failed", error=str(e), exc_info=True)
            return f"Failed to search documents: {str(e)}"

    return search_documents
