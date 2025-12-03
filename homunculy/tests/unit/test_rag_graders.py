"""Unit tests for RAG graders."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from internal.infrastructure.services.langgraph.rag.graders import (
    DocumentGrader,
    HallucinationGrader,
    AnswerGrader,
    GradeDocuments,
    GradeHallucinations,
    GradeAnswer,
)


class TestGradeDocuments:
    """Tests for GradeDocuments Pydantic model."""

    def test_valid_yes_score(self) -> None:
        """Should accept 'yes' score."""
        grade = GradeDocuments(binary_score="yes")
        assert grade.binary_score == "yes"

    def test_valid_no_score(self) -> None:
        """Should accept 'no' score."""
        grade = GradeDocuments(binary_score="no")
        assert grade.binary_score == "no"


class TestGradeHallucinations:
    """Tests for GradeHallucinations Pydantic model."""

    def test_valid_yes_score(self) -> None:
        """Should accept 'yes' for grounded."""
        grade = GradeHallucinations(binary_score="yes")
        assert grade.binary_score == "yes"


class TestGradeAnswer:
    """Tests for GradeAnswer Pydantic model."""

    def test_valid_no_score(self) -> None:
        """Should accept 'no' for not useful."""
        grade = GradeAnswer(binary_score="no")
        assert grade.binary_score == "no"


class TestDocumentGrader:
    """Tests for DocumentGrader."""

    @pytest.fixture
    def mock_grader(self) -> DocumentGrader:
        """Create grader with mocked LLM."""
        with patch("internal.infrastructure.services.langgraph.rag.graders.ChatOpenAI") as mock_llm:
            mock_instance = MagicMock()
            mock_llm.return_value = mock_instance
            grader = DocumentGrader(model="gpt-4o-mini")
            return grader

    @pytest.mark.asyncio
    async def test_grade_returns_true_for_relevant(self, mock_grader: DocumentGrader) -> None:
        """Should return True for relevant document."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.return_value = GradeDocuments(binary_score="yes")

        result = await mock_grader.grade(
            "What is Python?",
            "Python is a programming language.",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_grade_returns_false_for_irrelevant(self, mock_grader: DocumentGrader) -> None:
        """Should return False for irrelevant document."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.return_value = GradeDocuments(binary_score="no")

        result = await mock_grader.grade(
            "What is Python?",
            "The weather is sunny today.",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_grade_documents_filters_irrelevant(self, mock_grader: DocumentGrader) -> None:
        """Should filter out irrelevant documents."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.side_effect = [
            GradeDocuments(binary_score="yes"),
            GradeDocuments(binary_score="no"),
            GradeDocuments(binary_score="yes"),
        ]

        documents = [
            {"content": "Relevant doc 1", "id": "1"},
            {"content": "Irrelevant doc", "id": "2"},
            {"content": "Relevant doc 2", "id": "3"},
        ]

        result = await mock_grader.grade_documents("test query", documents)

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"


class TestHallucinationGrader:
    """Tests for HallucinationGrader."""

    @pytest.fixture
    def mock_grader(self) -> HallucinationGrader:
        """Create grader with mocked LLM."""
        with patch("internal.infrastructure.services.langgraph.rag.graders.ChatOpenAI") as mock_llm:
            mock_instance = MagicMock()
            mock_llm.return_value = mock_instance
            grader = HallucinationGrader(model="gpt-4o-mini")
            return grader

    @pytest.mark.asyncio
    async def test_check_returns_true_when_grounded(self, mock_grader: HallucinationGrader) -> None:
        """Should return True when answer is grounded."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.return_value = GradeHallucinations(binary_score="yes")

        result = await mock_grader.check(
            [{"content": "Python is a language."}],
            "Python is a programming language.",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_check_returns_false_when_hallucinating(
        self, mock_grader: HallucinationGrader
    ) -> None:
        """Should return False when answer has hallucination."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.return_value = GradeHallucinations(binary_score="no")

        result = await mock_grader.check(
            [{"content": "Python is a language."}],
            "Python was created in 2020.",
        )
        assert result is False

    def test_format_documents(self, mock_grader: HallucinationGrader) -> None:
        """Should format documents into single string."""
        documents = [
            {"content": "Doc 1"},
            {"content": "Doc 2"},
        ]
        result = mock_grader._format_documents(documents)
        assert result == "Doc 1\n\nDoc 2"


class TestAnswerGrader:
    """Tests for AnswerGrader."""

    @pytest.fixture
    def mock_grader(self) -> AnswerGrader:
        """Create grader with mocked LLM."""
        with patch("internal.infrastructure.services.langgraph.rag.graders.ChatOpenAI") as mock_llm:
            mock_instance = MagicMock()
            mock_llm.return_value = mock_instance
            grader = AnswerGrader(model="gpt-4o-mini")
            return grader

    @pytest.mark.asyncio
    async def test_grade_returns_true_for_useful_answer(self, mock_grader: AnswerGrader) -> None:
        """Should return True for useful answer."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.return_value = GradeAnswer(binary_score="yes")

        result = await mock_grader.grade(
            "What is Python?",
            "Python is a high-level programming language.",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_grade_returns_false_for_unhelpful_answer(
        self, mock_grader: AnswerGrader
    ) -> None:
        """Should return False for unhelpful answer."""
        mock_grader._grader = AsyncMock()
        mock_grader._grader.ainvoke.return_value = GradeAnswer(binary_score="no")

        result = await mock_grader.grade(
            "What is Python?",
            "I don't know anything about that.",
        )
        assert result is False
