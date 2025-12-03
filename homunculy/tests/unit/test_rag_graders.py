"""Unit tests for RAG graders."""

import pytest
from unittest.mock import AsyncMock

from internal.domain.services import LLMClient
from internal.infrastructure.services.langgraph.rag.schemas import (
    GradeDocumentsSchema,
    GradeHallucinationsSchema,
    GradeAnswerSchema,
)
from internal.infrastructure.services.langgraph.rag.document_grader import (
    OpenAIDocumentGrader,
)
from internal.infrastructure.services.langgraph.rag.hallucination_grader import (
    OpenAIHallucinationGrader,
)
from internal.infrastructure.services.langgraph.rag.answer_grader import (
    OpenAIAnswerGrader,
)


class TestGradeSchemas:
    """Tests for grading schema models."""

    def test_grade_documents_schema(self) -> None:
        """Should create valid document grade."""
        grade = GradeDocumentsSchema(binary_score="yes")
        assert grade.binary_score == "yes"

    def test_grade_hallucinations_schema(self) -> None:
        """Should create valid hallucination grade."""
        grade = GradeHallucinationsSchema(binary_score="no")
        assert grade.binary_score == "no"

    def test_grade_answer_schema(self) -> None:
        """Should create valid answer grade."""
        grade = GradeAnswerSchema(binary_score="yes")
        assert grade.binary_score == "yes"


class TestOpenAIDocumentGrader:
    """Tests for OpenAIDocumentGrader."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock LLM client."""
        return AsyncMock(spec=LLMClient)

    @pytest.fixture
    def grader(self, mock_client: AsyncMock) -> OpenAIDocumentGrader:
        """Create grader with mock client."""
        return OpenAIDocumentGrader(mock_client)

    @pytest.mark.asyncio
    async def test_grade_returns_true_for_relevant(
        self, grader: OpenAIDocumentGrader, mock_client: AsyncMock
    ) -> None:
        """Should return True for relevant document."""
        mock_client.invoke_structured.return_value = GradeDocumentsSchema(binary_score="yes")
        result = await grader.grade("What is Python?", "Python is a programming language.")
        assert result is True

    @pytest.mark.asyncio
    async def test_grade_returns_false_for_irrelevant(
        self, grader: OpenAIDocumentGrader, mock_client: AsyncMock
    ) -> None:
        """Should return False for irrelevant document."""
        mock_client.invoke_structured.return_value = GradeDocumentsSchema(binary_score="no")
        result = await grader.grade("What is Python?", "The weather is sunny.")
        assert result is False

    @pytest.mark.asyncio
    async def test_grade_batch_filters_documents(
        self, grader: OpenAIDocumentGrader, mock_client: AsyncMock
    ) -> None:
        """Should filter out irrelevant documents."""
        mock_client.invoke_structured.side_effect = [
            GradeDocumentsSchema(binary_score="yes"),
            GradeDocumentsSchema(binary_score="no"),
            GradeDocumentsSchema(binary_score="yes"),
        ]
        documents = [
            {"content": "Relevant 1", "id": "1"},
            {"content": "Irrelevant", "id": "2"},
            {"content": "Relevant 2", "id": "3"},
        ]
        result = await grader.grade_batch("test", documents)
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"


class TestOpenAIHallucinationGrader:
    """Tests for OpenAIHallucinationGrader."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock LLM client."""
        return AsyncMock(spec=LLMClient)

    @pytest.fixture
    def grader(self, mock_client: AsyncMock) -> OpenAIHallucinationGrader:
        """Create grader with mock client."""
        return OpenAIHallucinationGrader(mock_client)

    @pytest.mark.asyncio
    async def test_check_returns_true_when_grounded(
        self, grader: OpenAIHallucinationGrader, mock_client: AsyncMock
    ) -> None:
        """Should return True when grounded."""
        mock_client.invoke_structured.return_value = GradeHallucinationsSchema(binary_score="yes")
        result = await grader.check([{"content": "Python is a language."}], "Python is a language.")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_returns_false_when_hallucinating(
        self, grader: OpenAIHallucinationGrader, mock_client: AsyncMock
    ) -> None:
        """Should return False when hallucinating."""
        mock_client.invoke_structured.return_value = GradeHallucinationsSchema(binary_score="no")
        result = await grader.check(
            [{"content": "Python is a language."}], "Python was made in 2020."
        )
        assert result is False


class TestOpenAIAnswerGrader:
    """Tests for OpenAIAnswerGrader."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock LLM client."""
        return AsyncMock(spec=LLMClient)

    @pytest.fixture
    def grader(self, mock_client: AsyncMock) -> OpenAIAnswerGrader:
        """Create grader with mock client."""
        return OpenAIAnswerGrader(mock_client)

    @pytest.mark.asyncio
    async def test_grade_returns_true_for_useful(
        self, grader: OpenAIAnswerGrader, mock_client: AsyncMock
    ) -> None:
        """Should return True for useful answer."""
        mock_client.invoke_structured.return_value = GradeAnswerSchema(binary_score="yes")
        result = await grader.grade("What is Python?", "Python is a programming language.")
        assert result is True

    @pytest.mark.asyncio
    async def test_grade_returns_false_for_unhelpful(
        self, grader: OpenAIAnswerGrader, mock_client: AsyncMock
    ) -> None:
        """Should return False for unhelpful answer."""
        mock_client.invoke_structured.return_value = GradeAnswerSchema(binary_score="no")
        result = await grader.grade("What is Python?", "I don't know.")
        assert result is False
