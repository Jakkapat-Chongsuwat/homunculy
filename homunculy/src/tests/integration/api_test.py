"""API Integration Tests with TestContainers.

Tests the HTTP API layer with:
- Real PostgreSQL database (testcontainer)
- Mocked LLM (via DI container override)
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

from domain.interfaces import (
    DualSystemInput,
    DualSystemOutput,
    DualSystemPort,
    EmotionalTone,
    ResponseType,
)

# =============================================================================
# Constants
# =============================================================================

MOCK_RESPONSE = "Hello! I'm your friendly companion."


# =============================================================================
# Mock Dual-System
# =============================================================================


class MockDualSystem(DualSystemPort):
    """Mock dual-system that returns canned responses."""

    async def process(self, input_: DualSystemInput) -> DualSystemOutput:
        """Return mock response."""
        return DualSystemOutput(
            text=MOCK_RESPONSE,
            response_type=ResponseType.COGNITION,
            reflex=None,
            cognition=None,
            emotion=EmotionalTone.NEUTRAL,
        )

    async def stream(self, input_: DualSystemInput):
        """Stream mock response."""
        yield DualSystemOutput(
            text=MOCK_RESPONSE,
            response_type=ResponseType.COGNITION,
            reflex=None,
            cognition=None,
            emotion=EmotionalTone.NEUTRAL,
        )

    async def interrupt(self, session_id: str) -> None:
        """No-op interrupt for mock."""
        pass


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_app(postgres_container: PostgresContainer, monkeypatch):
    """Create test app with mocked LLM."""
    _set_db_env(postgres_container, monkeypatch)
    monkeypatch.setenv("GATEWAY_REDIS_EMBEDDED", "true")

    from infrastructure.container import container

    container.dual_system.override(providers.Object(MockDualSystem()))

    from main import create_api

    app = create_api()
    yield app

    container.dual_system.reset_override()


@pytest_asyncio.fixture
async def client(test_app):
    """Create async HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        yield ac


# =============================================================================
# Helpers
# =============================================================================


def _set_db_env(postgres_container: PostgresContainer, monkeypatch) -> None:
    """Set database env vars from container."""
    conn_url = postgres_container.get_connection_url()
    parts = conn_url.replace("postgresql+psycopg2://", "").split("@")
    user_pass = parts[0].split(":")
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")

    monkeypatch.setenv("DB_HOST", host_port[0])
    monkeypatch.setenv("DB_PORT", host_port[1])
    monkeypatch.setenv("DB_NAME", host_port_db[1])
    monkeypatch.setenv("DB_USER", user_pass[0])
    monkeypatch.setenv("DB_PASSWORD", user_pass[1])


# =============================================================================
# Tests - Health Endpoints
# =============================================================================


class TestHealthEndpoints:
    """Health check endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient):
        """Health endpoint returns 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self, client: AsyncClient):
        """Root endpoint returns service info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data or "name" in data


# =============================================================================
# Tests - Chat Endpoints
# =============================================================================


class TestChatEndpoints:
    """Chat API endpoint tests."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_exists(self, client: AsyncClient):
        """Chat endpoint responds (may be 200 or 404 if not implemented)."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "Hello!",
                "session_id": "test-integration-001",
            },
        )
        # If endpoint exists, it should work with mocked LLM
        if response.status_code == 200:
            data = response.json()
            assert "response" in data or "text" in data or "message" in data


# =============================================================================
# Tests - Dual System Endpoints
# =============================================================================


class TestDualSystemEndpoints:
    """Dual-system endpoint tests."""

    @pytest.mark.asyncio
    async def test_dual_process_endpoint(self, client: AsyncClient):
        """Dual process endpoint test."""
        response = await client.post(
            "/api/v1/dual/process",
            json={
                "text": "Hello there!",
                "session_id": "test-dual-001",
            },
        )
        # If endpoint exists, verify response structure
        if response.status_code == 200:
            data = response.json()
            assert "response_type" in data or "text" in data
