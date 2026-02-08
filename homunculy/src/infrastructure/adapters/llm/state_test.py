"""Unit tests for LangGraph state module."""

from infrastructure.adapters.llm.state import (
    GraphConfig,
    increment_retry,
    initial_state,
    with_documents,
    with_generation,
)


class TestGraphState:
    """Tests for GraphState TypedDict."""

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


class TestGraphConfig:
    """Tests for GraphConfig model."""

    def test_create_config(self) -> None:
        config = GraphConfig(thread_id="t1", agent_id="a1")
        assert config.thread_id == "t1"
        assert config.agent_id == "a1"
        assert config.max_retries == 3
        assert config.temperature == 0.7

    def test_config_custom_values(self) -> None:
        config = GraphConfig(
            thread_id="t2",
            agent_id="a2",
            max_retries=5,
            temperature=0.5,
        )
        assert config.max_retries == 5
        assert config.temperature == 0.5
