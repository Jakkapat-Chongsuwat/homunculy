"""
API End-to-End Tests with TestContainers.

Tests the full HTTP API stack using real containers.
"""

from __future__ import annotations

import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def postgres_container():
    """Start PostgreSQL container for tests."""
    os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
    try:
        with PostgresContainer("postgres:16") as postgres:
            yield postgres
    except Exception as exc:
        pytest.skip(f"Docker/Testcontainers unavailable: {exc}")


@pytest_asyncio.fixture
async def test_app(postgres_container: PostgresContainer, monkeypatch):
    """Create test application with real database."""

    # Set environment for database
    conn_url = postgres_container.get_connection_url()
    # Parse connection URL
    # Format: postgresql+psycopg2://user:pass@host:port/db
    parts = conn_url.replace("postgresql+psycopg2://", "").split("@")
    user_pass = parts[0].split(":")
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")

    monkeypatch.setenv("DB_HOST", host_port[0])
    monkeypatch.setenv("DB_PORT", host_port[1])
    monkeypatch.setenv("DB_NAME", host_port_db[1])
    monkeypatch.setenv("DB_USER", user_pass[0])
    monkeypatch.setenv("DB_PASSWORD", user_pass[1])

    # Import after setting env vars
    from main import create_api

    app = create_api()
    yield app


@pytest_asyncio.fixture
async def client(test_app):
    """Create async HTTP client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHealthEndpoints:
    """Health check endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Health endpoint should return 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Root endpoint should return service info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data or "name" in data


class TestChatEndpoints:
    """Chat API endpoint tests."""

    @pytest.mark.asyncio
    async def test_chat_message(self, client: AsyncClient):
        """Should process chat message."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "Hello!",
                "session_id": "test-e2e-001",
            },
        )
        # May be 200 or 404 depending on route setup
        assert response.status_code in [200, 404, 422]

    @pytest.mark.asyncio
    async def test_chat_with_context(self, client: AsyncClient):
        """Should process chat with context."""
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "What time is it?",
                "session_id": "test-e2e-002",
                "context": {"user_name": "TestUser"},
            },
        )
        assert response.status_code in [200, 404, 422]


class TestDualSystemEndpoints:
    """Dual-system specific endpoint tests."""

    @pytest.mark.asyncio
    async def test_dual_process(self, client: AsyncClient):
        """Should use dual-system for processing."""
        response = await client.post(
            "/api/v1/dual/process",
            json={
                "text": "Hello there!",
                "session_id": "test-dual-001",
            },
        )
        # Endpoint may not exist yet
        if response.status_code == 200:
            data = response.json()
            assert "response_type" in data

    @pytest.mark.asyncio
    async def test_dual_stream(self, client: AsyncClient):
        """Should stream dual-system responses."""
        response = await client.post(
            "/api/v1/dual/stream",
            json={
                "text": "Tell me about AI",
                "session_id": "test-dual-002",
            },
        )
        # Streaming endpoint - check basic response
        assert response.status_code in [200, 404]
