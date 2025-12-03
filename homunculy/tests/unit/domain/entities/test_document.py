"""Unit tests for Document entity."""

import pytest

from internal.domain.entities.document import Document


class TestDocument:
    """Tests for Document entity."""

    def test_create_document(self) -> None:
        """Should create document with all fields."""
        doc = Document(
            id="doc1",
            content="Test content",
            score=0.95,
            metadata={"source": "test"},
        )
        assert doc.id == "doc1"
        assert doc.content == "Test content"
        assert doc.score == 0.95
        assert doc.metadata == {"source": "test"}

    def test_create_document_optional_metadata(self) -> None:
        """Should create document without metadata."""
        doc = Document(id="doc1", content="Test", score=0.8)
        assert doc.metadata is None

    def test_from_dict(self) -> None:
        """Should create document from dictionary."""
        data = {
            "id": "doc1",
            "content": "Test content",
            "score": 0.9,
            "metadata": {"key": "value"},
        }
        doc = Document.from_dict(data)

        assert doc.id == "doc1"
        assert doc.content == "Test content"
        assert doc.score == 0.9
        assert doc.metadata == {"key": "value"}

    def test_from_dict_missing_fields(self) -> None:
        """Should handle missing fields with defaults."""
        doc = Document.from_dict({})

        assert doc.id == ""
        assert doc.content == ""
        assert doc.score == 0.0
        assert doc.metadata is None

    def test_is_relevant_above_threshold(self) -> None:
        """Should return True when score above threshold."""
        doc = Document(id="1", content="Test", score=0.8)
        assert doc.is_relevant(threshold=0.7) is True

    def test_is_relevant_at_threshold(self) -> None:
        """Should return True when score equals threshold."""
        doc = Document(id="1", content="Test", score=0.7)
        assert doc.is_relevant(threshold=0.7) is True

    def test_is_relevant_below_threshold(self) -> None:
        """Should return False when score below threshold."""
        doc = Document(id="1", content="Test", score=0.6)
        assert doc.is_relevant(threshold=0.7) is False

    def test_is_relevant_default_threshold(self) -> None:
        """Should use default threshold of 0.7."""
        high_doc = Document(id="1", content="Test", score=0.75)
        low_doc = Document(id="2", content="Test", score=0.65)

        assert high_doc.is_relevant() is True
        assert low_doc.is_relevant() is False
