"""Unit tests for Agent HTTP handler - testing public API behavior."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.entities.agent import AgentResponse
from infrastructure.container import container
from presentation.http.handlers.agent import router


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_llm() -> AsyncMock:
    """Create mock LLM service."""
    llm = AsyncMock()
    llm.chat.return_value = AgentResponse(message="Hello!", confidence=0.95)
    return llm


@pytest.fixture(autouse=True)
def reset_llm_adapter() -> None:
    """Reset container overrides after each test."""
    container.llm_adapter.override(None)
    yield
    container.llm_adapter.override(None)


class TestChatEndpoint:
    """Tests for POST /chat endpoint."""

    def test_returns_503_when_no_llm(self, client: TestClient) -> None:
        resp = client.post("/chat", json={"message": "Hi"})
        assert resp.status_code == 503

    def test_returns_response(self, client: TestClient, mock_llm: AsyncMock) -> None:
        container.llm_adapter.override(mock_llm)
        resp = client.post("/chat", json={"message": "Hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Hello!"
        assert data["confidence"] == 0.95

    def test_uses_default_thread_id(self, client: TestClient, mock_llm: AsyncMock) -> None:
        container.llm_adapter.override(mock_llm)
        resp = client.post("/chat", json={"message": "Hi"})
        assert resp.status_code == 200
        assert resp.json()["thread_id"] == "default"

    def test_uses_custom_thread_id(self, client: TestClient, mock_llm: AsyncMock) -> None:
        container.llm_adapter.override(mock_llm)
        resp = client.post("/chat", json={"message": "Hi", "thread_id": "custom-123"})
        assert resp.status_code == 200
        assert resp.json()["thread_id"] == "custom-123"

    def test_calls_llm_with_message(self, client: TestClient, mock_llm: AsyncMock) -> None:
        container.llm_adapter.override(mock_llm)
        client.post("/chat", json={"message": "Test message"})
        mock_llm.chat.assert_called_once()
        call_args = mock_llm.chat.call_args[0]
        assert call_args[1] == "Test message"


class TestChatStreamEndpoint:
    """Tests for POST /chat/stream endpoint."""

    def test_returns_503_when_no_llm(self, client: TestClient) -> None:
        resp = client.post("/chat/stream", json={"message": "Hi"})
        assert resp.status_code == 503

    def test_returns_streaming_response(self, client: TestClient, mock_llm: AsyncMock) -> None:
        async def mock_stream(*args, **kwargs):
            yield "chunk1"
            yield "chunk2"

        mock_llm.stream_chat = mock_stream
        container.llm_adapter.override(mock_llm)
        resp = client.post("/chat/stream", json={"message": "Hello"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"
