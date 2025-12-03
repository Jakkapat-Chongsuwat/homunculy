"""RAG State Definition."""

from typing import List, TypedDict, Annotated, Optional
from operator import add


class RAGState(TypedDict, total=False):
    """State for self-reflective RAG workflow.

    Attributes:
        question: The user's input question.
        documents: List of retrieved documents with content and scores.
        generation: The generated answer.
        retrieval_attempts: Number of retrieval attempts made.
        max_retrieval_attempts: Maximum allowed retrieval attempts.
        web_search_needed: Whether to perform web search.
        documents_relevant: Whether retrieved documents are relevant.
        hallucination_detected: Whether hallucination was detected.
        answer_useful: Whether the answer addresses the question.
        rewritten_query: Query after transformation.
    """

    question: str
    documents: Annotated[List[dict], add]
    generation: str
    retrieval_attempts: int
    max_retrieval_attempts: int
    web_search_needed: bool
    documents_relevant: bool
    hallucination_detected: bool
    answer_useful: bool
    rewritten_query: Optional[str]


def create_initial_state(
    question: str,
    max_attempts: int = 3,
) -> RAGState:
    """Create initial RAG state."""
    return RAGState(
        question=question,
        documents=[],
        generation="",
        retrieval_attempts=0,
        max_retrieval_attempts=max_attempts,
        web_search_needed=False,
        documents_relevant=False,
        hallucination_detected=False,
        answer_useful=False,
        rewritten_query=None,
    )
