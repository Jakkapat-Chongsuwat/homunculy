"""Retrieve node - Fetch documents from RAG."""

from typing import Any

from application.graphs.state import GraphStateBase, with_documents
from common.logger import get_logger
from domain.interfaces import RAGPort

logger = get_logger(__name__)


async def retrieve_node(
    state: GraphStateBase,
    rag: RAGPort,
    top_k: int = 5,
) -> GraphStateBase:
    """Retrieve relevant documents for the question."""
    question = _extract_question(state)
    documents = await _fetch_documents(rag, question, top_k)
    return with_documents(state, documents)


def _extract_question(state: GraphStateBase) -> str:
    """Extract question from state."""
    return state.get("question", "")


async def _fetch_documents(
    rag: RAGPort,
    question: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """Fetch documents from RAG service."""
    logger.debug("Retrieving documents", query=question, top_k=top_k)
    return await rag.retrieve(question, top_k=top_k)
