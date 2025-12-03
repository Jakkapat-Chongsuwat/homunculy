"""Unit tests for RAG state module."""

import pytest
from internal.infrastructure.services.langgraph.rag.state import (
    RAGState,
    create_initial_state,
)


class TestRAGState:
    """Tests for RAGState TypedDict."""

    def test_rag_state_has_required_fields(self) -> None:
        """RAGState should have all required fields."""
        state: RAGState = {
            "question": "test question",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": 3,
        }
        assert state["question"] == "test question"
        assert state["documents"] == []
        assert state["generation"] == ""

    def test_rag_state_optional_fields(self) -> None:
        """RAGState should support optional fields."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": 3,
            "web_search_needed": True,
            "documents_relevant": False,
            "rewritten_query": "better query",
        }
        assert state["web_search_needed"] is True
        assert state["documents_relevant"] is False
        assert state["rewritten_query"] == "better query"


class TestCreateInitialState:
    """Tests for create_initial_state factory."""

    def test_creates_state_with_question(self) -> None:
        """Should create state with provided question."""
        state = create_initial_state("What is RAG?")
        assert state["question"] == "What is RAG?"

    def test_creates_state_with_empty_documents(self) -> None:
        """Should initialize with empty documents list."""
        state = create_initial_state("test")
        assert state["documents"] == []

    def test_creates_state_with_zero_attempts(self) -> None:
        """Should start with zero retrieval attempts."""
        state = create_initial_state("test")
        assert state["retrieval_attempts"] == 0

    def test_creates_state_with_default_max_attempts(self) -> None:
        """Should have default max attempts of 3."""
        state = create_initial_state("test")
        assert state["max_retrieval_attempts"] == 3

    def test_creates_state_with_custom_max_attempts(self) -> None:
        """Should accept custom max attempts."""
        state = create_initial_state("test", max_attempts=5)
        assert state["max_retrieval_attempts"] == 5

    def test_creates_state_with_false_flags(self) -> None:
        """Should initialize boolean flags to False."""
        state = create_initial_state("test")
        assert state["web_search_needed"] is False
        assert state["documents_relevant"] is False
        assert state["hallucination_detected"] is False
        assert state["answer_useful"] is False

    def test_creates_state_with_empty_generation(self) -> None:
        """Should start with empty generation."""
        state = create_initial_state("test")
        assert state["generation"] == ""

    def test_creates_state_with_none_rewritten_query(self) -> None:
        """Should start with no rewritten query."""
        state = create_initial_state("test")
        assert state["rewritten_query"] is None
