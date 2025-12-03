"""Unit tests for RAG nodes."""

import pytest
from unittest.mock import AsyncMock

from internal.domain.services import (
    RAGService,
    LLMClient,
    DocumentGraderService,
    HallucinationGraderService,
    AnswerGraderService,
    QueryRewriterService,
)
from internal.infrastructure.services.langgraph.rag.nodes import RAGNodes
from internal.infrastructure.services.langgraph.rag.state import RAGState


class TestRAGNodes:
    """Tests for RAGNodes."""

    @pytest.fixture
    def mock_rag_service(self) -> AsyncMock:
        """Create mock RAG service."""
        service = AsyncMock(spec=RAGService)
        service.retrieve.return_value = [{"id": "1", "content": "Test doc", "score": 0.9}]
        service.search_web.return_value = [{"id": "web1", "content": "Web result", "score": 0.8}]
        return service

    @pytest.fixture
    def mock_llm_client(self) -> AsyncMock:
        """Create mock LLM client."""
        client = AsyncMock(spec=LLMClient)
        client.invoke.return_value = "Generated response"
        return client

    @pytest.fixture
    def mock_doc_grader(self) -> AsyncMock:
        """Create mock document grader."""
        grader = AsyncMock(spec=DocumentGraderService)
        grader.grade_batch.return_value = [{"content": "Relevant", "id": "1"}]
        return grader

    @pytest.fixture
    def mock_hallucination_grader(self) -> AsyncMock:
        """Create mock hallucination grader."""
        return AsyncMock(spec=HallucinationGraderService)

    @pytest.fixture
    def mock_answer_grader(self) -> AsyncMock:
        """Create mock answer grader."""
        return AsyncMock(spec=AnswerGraderService)

    @pytest.fixture
    def mock_query_rewriter(self) -> AsyncMock:
        """Create mock query rewriter."""
        rewriter = AsyncMock(spec=QueryRewriterService)
        rewriter.rewrite.return_value = "improved query"
        return rewriter

    @pytest.fixture
    def nodes(
        self,
        mock_rag_service: AsyncMock,
        mock_llm_client: AsyncMock,
        mock_doc_grader: AsyncMock,
        mock_hallucination_grader: AsyncMock,
        mock_answer_grader: AsyncMock,
        mock_query_rewriter: AsyncMock,
    ) -> RAGNodes:
        """Create RAGNodes with all mocked dependencies."""
        return RAGNodes(
            rag_service=mock_rag_service,
            llm_client=mock_llm_client,
            doc_grader=mock_doc_grader,
            hallucination_grader=mock_hallucination_grader,
            answer_grader=mock_answer_grader,
            query_rewriter=mock_query_rewriter,
        )

    @pytest.mark.asyncio
    async def test_retrieve_calls_rag_service(
        self, nodes: RAGNodes, mock_rag_service: AsyncMock
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
        self, nodes: RAGNodes, mock_rag_service: AsyncMock
    ) -> None:
        """Should use rewritten query if available."""
        state: RAGState = {
            "question": "What is RAG?",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": 3,
            "rewritten_query": "better query",
        }
        await nodes.retrieve(state)
        mock_rag_service.retrieve.assert_called_once_with("better query", top_k=5)

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
    async def test_grade_documents_marks_relevant(
        self, nodes: RAGNodes, mock_doc_grader: AsyncMock
    ) -> None:
        """Should mark documents as relevant when found."""
        mock_doc_grader.grade_batch.return_value = [{"content": "Relevant", "id": "1"}]
        state: RAGState = {
            "question": "test",
            "documents": [{"content": "Relevant", "id": "1"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }
        result = await nodes.grade_documents(state)
        assert result["documents_relevant"] is True
        assert result["web_search_needed"] is False

    @pytest.mark.asyncio
    async def test_grade_documents_marks_irrelevant(
        self, nodes: RAGNodes, mock_doc_grader: AsyncMock
    ) -> None:
        """Should mark documents as irrelevant when none pass."""
        mock_doc_grader.grade_batch.return_value = []
        state: RAGState = {
            "question": "test",
            "documents": [{"content": "Irrelevant", "id": "1"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }
        result = await nodes.grade_documents(state)
        assert result["documents_relevant"] is False
        assert result["web_search_needed"] is True

    @pytest.mark.asyncio
    async def test_transform_query_rewrites(
        self, nodes: RAGNodes, mock_query_rewriter: AsyncMock
    ) -> None:
        """Should rewrite query and reset documents."""
        mock_query_rewriter.rewrite.return_value = "improved query"
        state: RAGState = {
            "question": "what is rag",
            "documents": [{"content": "old doc"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }
        result = await nodes.transform_query(state)
        assert result["rewritten_query"] == "improved query"
        assert result["documents"] == []

    @pytest.mark.asyncio
    async def test_generate_creates_response(
        self, nodes: RAGNodes, mock_llm_client: AsyncMock
    ) -> None:
        """Should generate answer from documents."""
        mock_llm_client.invoke.return_value = "RAG is a technique..."
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
    async def test_check_hallucination_detects_grounded(
        self, nodes: RAGNodes, mock_hallucination_grader: AsyncMock
    ) -> None:
        """Should detect grounded answers."""
        mock_hallucination_grader.check.return_value = True
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
    async def test_check_hallucination_detects_hallucination(
        self, nodes: RAGNodes, mock_hallucination_grader: AsyncMock
    ) -> None:
        """Should detect hallucinations."""
        mock_hallucination_grader.check.return_value = False
        state: RAGState = {
            "question": "test",
            "documents": [{"content": "fact"}],
            "generation": "Made up...",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
        }
        result = await nodes.check_hallucination(state)
        assert result["hallucination_detected"] is True

    @pytest.mark.asyncio
    async def test_check_answer_grades_useful(
        self, nodes: RAGNodes, mock_answer_grader: AsyncMock
    ) -> None:
        """Should grade answer as useful."""
        mock_answer_grader.grade.return_value = True
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
        self, nodes: RAGNodes, mock_rag_service: AsyncMock
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
        documents = [{"content": "First."}, {"content": "Second."}]
        result = nodes.format_context(documents)
        assert result == "First.\n\nSecond."

    def test_build_prompt(self, nodes: RAGNodes) -> None:
        """Should build proper generation prompt."""
        result = nodes.build_prompt("test question", "context")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
