"""RAG State Definition."""

from typing import List, TypedDict, Annotated, Optional, NotRequired
from operator import add


class RAGState(TypedDict):
    """State for self-reflective RAG workflow."""

    question: str
    documents: Annotated[List[dict], add]
    generation: str
    retrieval_attempts: int
    max_retrieval_attempts: int
    web_search_needed: NotRequired[bool]
    documents_relevant: NotRequired[bool]
    hallucination_detected: NotRequired[bool]
    answer_useful: NotRequired[bool]
    rewritten_query: NotRequired[Optional[str]]


def create_initial_state(question: str, max_attempts: int = 3) -> RAGState:
    """Create initial RAG state."""
    return RAGState(
        question=question,
        documents=[],
        generation="",
        retrieval_attempts=0,
        max_retrieval_attempts=max_attempts,
    )
