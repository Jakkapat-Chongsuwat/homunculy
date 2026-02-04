"""Graph state types - framework agnostic.

These are pure TypedDicts without any framework-specific reducers.
The infrastructure layer (LangGraph) uses its own GraphState with reducers.

Application layer nodes use this for type hints - it's structurally
compatible with infrastructure's GraphState.
"""

from typing import Any

from typing_extensions import TypedDict


class GraphStateBase(TypedDict):
    """Base graph state for type hints in application layer.

    Structurally compatible with infrastructure.adapters.langgraph.state.GraphState.
    Use this in application layer for framework-agnostic type hints.
    """

    messages: list[Any]
    question: str
    generation: str
    documents: list[dict[str, Any]]
    retry_count: int


def initial_state(question: str) -> GraphStateBase:
    """Create initial graph state."""
    return {
        "messages": [],
        "question": question,
        "generation": "",
        "documents": [],
        "retry_count": 0,
    }


def with_documents(state: GraphStateBase, docs: list[dict]) -> GraphStateBase:
    """Return state with documents added."""
    return {**state, "documents": docs}


def with_generation(state: GraphStateBase, text: str) -> GraphStateBase:
    """Return state with generation set."""
    return {**state, "generation": text}


def increment_retry(state: GraphStateBase) -> GraphStateBase:
    """Return state with retry count incremented."""
    return {**state, "retry_count": state["retry_count"] + 1}
