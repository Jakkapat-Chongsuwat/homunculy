"""Rewrite node - Transform query for better retrieval."""

from common.logger import get_logger

from application.graphs.state import GraphState

logger = get_logger(__name__)


async def rewrite_query_node(
    state: GraphState,
    rewriter_fn,
) -> GraphState:
    """Rewrite query for better retrieval."""
    question = state.get("question", "")
    rewritten = await _rewrite(question, rewriter_fn)
    return {**state, "question": rewritten}


async def _rewrite(question: str, rewriter_fn) -> str:
    """Invoke rewriter and return improved query."""
    logger.debug("Rewriting query", original=question)
    result = await rewriter_fn(question)
    return _extract_rewritten(result)


def _extract_rewritten(result) -> str:
    """Extract rewritten query from result."""
    if isinstance(result, str):
        return result
    return result.get("query", result.get("question", str(result)))
