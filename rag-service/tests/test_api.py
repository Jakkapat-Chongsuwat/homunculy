"""
Test RAG API endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

# Note: These tests require Pinecone Local running
# Start with: docker run -d --name pinecone-local -e PORT=5081 -e INDEX_TYPE=serverless -e DIMENSION=1536 -e METRIC=cosine -p 5081:5081 ghcr.io/pinecone-io/pinecone-index:latest


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Clean Architecture is a software design philosophy that separates code into layers.
    The innermost layer contains business logic and entities.
    The outer layers contain frameworks, databases, and UI.
    Dependencies should point inward, not outward.
    This makes the code more testable and maintainable.
    """


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {"source": "test", "category": "architecture", "title": "Clean Architecture Overview"}


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self):
        """Health endpoint should return healthy status."""
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Test root endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self):
        """Root endpoint should return service information."""
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "rag-service"
        assert "version" in data
