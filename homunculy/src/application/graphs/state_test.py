"""Unit tests for Graph state module (application layer)."""

from application.graphs.state import (
    GraphStateBase,
    increment_retry,
    initial_state,
    with_documents,
    with_generation,
)


class TestGraphStateBase:
    """Tests for GraphStateBase TypedDict."""

    def test_initial_state(self) -> None:
        state = initial_state("What is AI?")
        assert state["question"] == "What is AI?"
        assert state["messages"] == []
        assert state["generation"] == ""
        assert state["documents"] == []
        assert state["retry_count"] == 0

    def test_with_documents(self) -> None:
        state = initial_state("Question")
        docs = [{"content": "doc1"}, {"content": "doc2"}]
        new_state = with_documents(state, docs)
        assert len(new_state["documents"]) == 2
        assert new_state["question"] == "Question"

    def test_with_generation(self) -> None:
        state = initial_state("Q")
        new_state = with_generation(state, "Answer text")
        assert new_state["generation"] == "Answer text"

    def test_increment_retry(self) -> None:
        state = initial_state("Q")
        assert state["retry_count"] == 0
        new_state = increment_retry(state)
        assert new_state["retry_count"] == 1

    def test_immutability(self) -> None:
        state = initial_state("Q")
        new_state = with_generation(state, "Answer")
        assert state["generation"] == ""
        assert new_state["generation"] == "Answer"

    def test_type_compatibility(self) -> None:
        """Verify the state is a valid TypedDict."""
        state: GraphStateBase = initial_state("Q")
        assert isinstance(state, dict)
        assert "messages" in state
        assert "question" in state
        assert "generation" in state
        assert "documents" in state
        assert "retry_count" in state
