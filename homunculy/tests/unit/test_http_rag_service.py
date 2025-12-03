"""Unit tests for HTTP RAG service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from internal.infrastructure.services.rag.http_rag_service import HTTPRAGService


class TestHTTPRAGService:
    """Tests for HTTPRAGService."""

    @pytest.fixture
    def service(self) -> HTTPRAGService:
        """Create HTTP RAG service."""
        return HTTPRAGService(base_url="http://localhost:8001")

    def test_init_sets_base_url(self) -> None:
        """Should set base URL correctly."""
        service = HTTPRAGService(base_url="http://test:8000/")
        assert service.base_url == "http://test:8000"

    def test_init_strips_trailing_slash(self) -> None:
        """Should strip trailing slash from URL."""
        service = HTTPRAGService(base_url="http://test:8000/")
        assert not service.base_url.endswith("/")

    def test_init_sets_timeout(self) -> None:
        """Should set custom timeout."""
        service = HTTPRAGService(timeout=60.0)
        assert service.timeout == 60.0

    @pytest.mark.asyncio
    async def test_retrieve_calls_api(self, service: HTTPRAGService) -> None:
        """Should call RAG API with correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "1", "content": "Test doc", "score": 0.9}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            await service.retrieve(
                query="test query",
                top_k=5,
                namespace="default",
            )

            mock_instance.post.assert_called_once()
            call_args = mock_instance.post.call_args
            assert call_args[0][0] == "http://localhost:8001/api/v1/query"
            assert call_args[1]["json"]["query"] == "test query"

    @pytest.mark.asyncio
    async def test_retrieve_returns_parsed_results(self, service: HTTPRAGService) -> None:
        """Should parse API response correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "doc1",
                    "content": "Document content",
                    "score": 0.85,
                    "metadata": {"source": "test"},
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await service.retrieve("test")

            assert len(result) == 1
            assert result[0]["id"] == "doc1"
            assert result[0]["content"] == "Document content"
            assert result[0]["score"] == 0.85
            assert result[0]["metadata"]["source"] == "test"

    @pytest.mark.asyncio
    async def test_search_web_returns_empty_list(self, service: HTTPRAGService) -> None:
        """Should return empty list (placeholder)."""
        result = await service.search_web("test query")
        assert result == []

    def test_parse_results_handles_empty(self, service: HTTPRAGService) -> None:
        """Should handle empty results."""
        result = service.parse_results({"results": []})
        assert result == []

    def test_parse_results_handles_missing_fields(self, service: HTTPRAGService) -> None:
        """Should handle missing fields with defaults."""
        data = {"results": [{"id": "1"}]}
        result = service.parse_results(data)

        assert result[0]["id"] == "1"
        assert result[0]["content"] == ""
        assert result[0]["score"] == 0.0
        assert result[0]["metadata"] is None

    def test_parse_results_handles_no_results_key(self, service: HTTPRAGService) -> None:
        """Should handle missing results key."""
        result = service.parse_results({})
        assert result == []
