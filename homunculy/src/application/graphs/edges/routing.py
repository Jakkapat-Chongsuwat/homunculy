"""Routing logic for graph edges."""

from application.graphs.state import GraphStateBase

# Node name constants
NODE_GENERATE = "generate"
NODE_REWRITE = "rewrite"
NODE_END = "__end__"


def route_question(state: GraphStateBase, has_docs_fn) -> str:
    """Route based on document availability."""
    docs = state.get("documents", [])
    return NODE_GENERATE if has_docs_fn(docs) else NODE_REWRITE


def decide_to_generate(state: GraphStateBase) -> str:
    """Decide whether to generate or rewrite."""
    docs = state.get("documents", [])
    return NODE_GENERATE if _has_relevant_docs(docs) else NODE_REWRITE


def _has_relevant_docs(docs: list[dict]) -> bool:
    """Check if we have relevant documents."""
    return len(docs) > 0


def grade_generation_route(grade_result: dict) -> str:
    """Route based on generation grade."""
    if not _is_grounded(grade_result):
        return NODE_REWRITE
    if not _is_useful(grade_result):
        return NODE_REWRITE
    return NODE_END


def _is_grounded(result: dict) -> bool:
    """Check if generation is grounded."""
    return result.get("grounded", False)


def _is_useful(result: dict) -> bool:
    """Check if generation is useful."""
    return result.get("useful", False)
