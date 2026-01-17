"""Graph state schema for LangGraph workflows."""

from typing import Annotated, Any

from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class GraphState(TypedDict):
    """State for RAG-enhanced conversation graph."""

    messages: Annotated[list[Any], add_messages]
    question: str
    generation: str
    documents: list[dict[str, Any]]
    retry_count: int


class GraphConfig(BaseModel):
    """Graph configuration."""

    max_retries: int = Field(default=3, ge=1)
    thread_id: str = Field(...)
    agent_id: str = Field(...)
    temperature: float = Field(default=0.7)


def initial_state(question: str) -> GraphState:
    """Create initial graph state."""
    return {
        "messages": [],
        "question": question,
        "generation": "",
        "documents": [],
        "retry_count": 0,
    }


def with_documents(state: GraphState, docs: list[dict]) -> GraphState:
    """Return state with documents added."""
    return {**state, "documents": docs}


def with_generation(state: GraphState, text: str) -> GraphState:
    """Return state with generation set."""
    return {**state, "generation": text}


def increment_retry(state: GraphState) -> GraphState:
    """Return state with incremented retry count."""
    return {**state, "retry_count": state["retry_count"] + 1}
