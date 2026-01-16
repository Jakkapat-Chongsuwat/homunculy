"""Unit tests for query rewriter."""

from unittest.mock import AsyncMock

import pytest

from internal.domain.services import LLMClient
from internal.infrastructure.services.langgraph.rag.query_rewriter import (
    QUERY_REWRITER_PROMPT,
    OpenAIQueryRewriter,
)


class TestOpenAIQueryRewriter:
    """Tests for OpenAIQueryRewriter."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create mock LLM client."""
        client = AsyncMock(spec=LLMClient)
        client.invoke.return_value = "improved query"
        return client

    @pytest.fixture
    def rewriter(self, mock_client: AsyncMock) -> OpenAIQueryRewriter:
        """Create rewriter with mock client."""
        return OpenAIQueryRewriter(mock_client)

    @pytest.mark.asyncio
    async def test_rewrite_returns_improved_query(
        self, rewriter: OpenAIQueryRewriter, mock_client: AsyncMock
    ) -> None:
        """Should return improved query from LLM."""
        mock_client.invoke.return_value = "retrieval augmented generation explanation"
        result = await rewriter.rewrite("what is rag")
        assert result == "retrieval augmented generation explanation"

    @pytest.mark.asyncio
    async def test_rewrite_calls_client_with_messages(
        self, rewriter: OpenAIQueryRewriter, mock_client: AsyncMock
    ) -> None:
        """Should call client with correct messages."""
        await rewriter.rewrite("original query")
        mock_client.invoke.assert_called_once()
        call_args = mock_client.invoke.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["role"] == "system"
        assert call_args[1]["role"] == "user"
        assert call_args[1]["content"] == "original query"

    def test_prompt_is_defined(self) -> None:
        """Should have a prompt defined."""
        assert QUERY_REWRITER_PROMPT is not None
        assert "vectorstore" in QUERY_REWRITER_PROMPT
