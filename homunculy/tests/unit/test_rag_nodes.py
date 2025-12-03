"""Unit tests for RAG nodes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from internal.infrastructure.services.langgraph.rag.nodes import RAGNodes
from internal.infrastructure.services.langgraph.rag.state import RAGState


class TestRAGNodes:
    """Tests for RAGNodes."""

    @pytest.fixture
    def mock_rag_service(self) -> AsyncMock:
        """Create mock RAG service."""
        service = AsyncMock()
        service.retrieve.return_value = [
            {"id": "1", "content": "Test doc", "score": 0.9},
        ]
        service.search_web.return_value = [
            {"id": "web1", "content": "Web result", "score": 0.8},
        ]
        return service

    @pytest.fixture
    def nodes(self, mock_rag_service: AsyncMock) -> RAGNodes:
        """Create RAGNodes with mocked dependencies."""
        with patch("internal.infrastructure.services.langgraph.rag.nodes.ChatOpenAI"):
            return RAGNodes(mock_rag_service, model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_retrieve_calls_rag_service(
        self,
        nodes: RAGNodes,
        mock_rag_service: AsyncMock,
    ) -> None:
        """Should call RAG service with query."""
        state: RAGState = {
            "question": "What is RAG?",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.retrieve(state)

        mock_rag_service.retrieve.assert_called_once_with("What is RAG?", top_k=5)
        assert len(result["documents"]) == 1

    @pytest.mark.asyncio
    async def test_retrieve_uses_rewritten_query(
        self,
        nodes: RAGNodes,
        mock_rag_service: AsyncMock,
    ) -> None:
        """Should use rewritten query if available."""
        state: RAGState = {
            "question": "What is RAG?",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": 3,
            "rewritten_query": "retrieval augmented generation explanation",
        }

        await nodes.retrieve(state)

        mock_rag_service.retrieve.assert_called_once_with(
            "retrieval augmented generation explanation", top_k=5
        )

    @pytest.mark.asyncio
    async def test_retrieve_increments_attempts(self, nodes: RAGNodes) -> None:
        """Should increment retrieval attempts."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.retrieve(state)

        assert result["retrieval_attempts"] == 2

    @pytest.mark.asyncio
    async def test_grade_documents_marks_relevant(self, nodes: RAGNodes) -> None:
        """Should mark documents as relevant when found."""
        nodes._doc_grader.grade_documents = AsyncMock(
            return_value=[{"content": "Relevant doc", "id": "1"}]
        )

        state: RAGState = {
            "question": "test",
            "documents": [{"content": "Relevant doc", "id": "1"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.grade_documents(state)

        assert result["documents_relevant"] is True
        assert result["web_search_needed"] is False

    @pytest.mark.asyncio
    async def test_grade_documents_marks_irrelevant(self, nodes: RAGNodes) -> None:
        """Should mark documents as irrelevant when none pass."""
        nodes._doc_grader.grade_documents = AsyncMock(return_value=[])

        state: RAGState = {
            "question": "test",
            "documents": [{"content": "Irrelevant doc", "id": "1"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.grade_documents(state)

        assert result["documents_relevant"] is False
        assert result["web_search_needed"] is True

    @pytest.mark.asyncio
    async def test_transform_query_rewrites(self, nodes: RAGNodes) -> None:
        """Should rewrite query and reset documents."""
        nodes._query_rewriter.rewrite = AsyncMock(return_value="improved query for vectorstore")

        state: RAGState = {
            "question": "what is rag",
            "documents": [{"content": "old doc"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.transform_query(state)

        assert result["rewritten_query"] == "improved query for vectorstore"
        assert result["documents"] == []

    @pytest.mark.asyncio
    async def test_generate_creates_response(self, nodes: RAGNodes) -> None:
        """Should generate answer from documents."""
        mock_response = MagicMock()
        mock_response.content = "RAG is a technique..."
        nodes._llm.ainvoke = AsyncMock(return_value=mock_response)

        state: RAGState = {
            "question": "What is RAG?",
            "documents": [{"content": "RAG combines retrieval..."}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.generate(state)

        assert result["generation"] == "RAG is a technique..."

    @pytest.mark.asyncio
    async def test_check_hallucination_detects_grounded(self, nodes: RAGNodes) -> None:
        """Should detect grounded answers."""
        nodes._hallucination_grader.check = AsyncMock(return_value=True)

        state: RAGState = {
            "question": "test",
            "documents": [{"content": "fact"}],
            "generation": "Based on fact...",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.check_hallucination(state)

        assert result["hallucination_detected"] is False

    @pytest.mark.asyncio
    async def test_check_hallucination_detects_hallucination(self, nodes: RAGNodes) -> None:
        """Should detect hallucinations."""
        nodes._hallucination_grader.check = AsyncMock(return_value=False)

        state: RAGState = {
            "question": "test",
            "documents": [{"content": "fact"}],
            "generation": "Made up answer...",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.check_hallucination(state)

        assert result["hallucination_detected"] is True

    @pytest.mark.asyncio
    async def test_check_answer_grades_useful(self, nodes: RAGNodes) -> None:
        """Should grade answer as useful."""
        nodes._answer_grader.grade = AsyncMock(return_value=True)

        state: RAGState = {
            "question": "What is Python?",
            "documents": [],
            "generation": "Python is a programming language.",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.check_answer(state)

        assert result["answer_useful"] is True

    @pytest.mark.asyncio
    async def test_web_search_returns_results(
        self,
        nodes: RAGNodes,
        mock_rag_service: AsyncMock,
    ) -> None:
        """Should return web search results."""
        state: RAGState = {
            "question": "What is RAG?",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 3,
            "max_retrieval_attempts": 3,
        }

        result = await nodes.web_search(state)

        mock_rag_service.search_web.assert_called_once()
        assert len(result["documents"]) == 1

    def test_format_context(self, nodes: RAGNodes) -> None:
        """Should format documents into context string."""
        documents = [
            {"content": "First document."},
            {"content": "Second document."},
        ]

        result = nodes._format_context(documents)

        assert result == "First document.\n\nSecond document."

    def test_build_generation_prompt(self, nodes: RAGNodes) -> None:
        """Should build proper generation prompt."""
        result = nodes._build_generation_prompt("test question", "context")

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert "context" in result[1]["content"]
        assert "test question" in result[1]["content"]
