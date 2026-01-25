"""
Shared test fixtures for E2E tests.

Provides:
- PostgreSQL container
- Database URL
- Checkpointer
- Mock services
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from testcontainers.postgres import PostgresContainer

# =============================================================================
# Event Loop
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Containers
# =============================================================================


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start PostgreSQL container for tests.

    Scope: session - reused across all tests for speed.
    """
    container = PostgresContainer(
        image="postgres:16",
        username="test",
        password="test",
        dbname="homunculy_test",
    )
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def db_url(postgres_container: PostgresContainer) -> str:
    """Get database URL from container."""
    url = postgres_container.get_connection_url()
    # Convert to asyncpg format
    return url.replace("postgresql+psycopg2://", "postgresql://")


@pytest.fixture
def db_env(postgres_container: PostgresContainer, monkeypatch):
    """Set database environment variables."""
    url = postgres_container.get_connection_url()
    # Parse: postgresql+psycopg2://user:pass@host:port/db
    parts = url.replace("postgresql+psycopg2://", "").split("@")
    user_pass = parts[0].split(":")
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")

    monkeypatch.setenv("DB_HOST", host_port[0])
    monkeypatch.setenv("DB_PORT", host_port[1])
    monkeypatch.setenv("DB_NAME", host_port_db[1])
    monkeypatch.setenv("DB_USER", user_pass[0])
    monkeypatch.setenv("DB_PASSWORD", user_pass[1])


# =============================================================================
# Checkpointer
# =============================================================================


@pytest.fixture
async def checkpointer(db_url: str) -> AsyncGenerator:
    """Create checkpointer connected to test database."""
    from infrastructure.persistence import CheckpointerFactory

    uow = await CheckpointerFactory.create_postgres(db_url)
    yield uow.checkpointer
    await uow.cleanup()


@pytest.fixture
def memory_checkpointer():
    """Create in-memory checkpointer for fast tests."""
    from infrastructure.persistence import CheckpointerFactory

    return CheckpointerFactory.create_memory()


# =============================================================================
# Dual-System Components
# =============================================================================


@pytest.fixture
def reflex_adapter():
    """Create reflex adapter for testing."""
    from infrastructure.adapters.factory import create_reflex

    return create_reflex()


@pytest.fixture
def emotion_detector():
    """Create emotion detector for testing."""
    from infrastructure.adapters.factory import create_emotion_detector

    return create_emotion_detector()


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator for testing without LLM calls."""
    from domain.interfaces import (
        OrchestrationInput,
        OrchestrationOutput,
        OrchestratorPort,
    )

    class MockOrchestrator(OrchestratorPort):
        async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
            return OrchestrationOutput(
                message=f"Mock response to: {input_.message[:50]}",
                tool_calls=None,
                metadata={"mock": True},
            )

        async def stream(self, input_: OrchestrationInput):
            yield f"Mock streaming: {input_.message[:30]}"

    return MockOrchestrator()


@pytest.fixture
def cognition_adapter(mock_orchestrator):
    """Create cognition adapter with mock orchestrator."""
    from infrastructure.adapters.factory import create_cognition

    return create_cognition(orchestrator=mock_orchestrator)


@pytest.fixture
def dual_system(reflex_adapter, cognition_adapter, emotion_detector):
    """Create full dual-system for testing."""
    from infrastructure.adapters.factory import create_dual_system

    return create_dual_system(
        reflex=reflex_adapter,
        cognition=cognition_adapter,
        emotion=emotion_detector,
    )


# =============================================================================
# Test Helpers
# =============================================================================


@pytest.fixture
def sample_dual_input():
    """Create sample dual-system input."""
    from domain.interfaces import DualSystemInput

    def _create(text: str, session_id: str = "test-session") -> DualSystemInput:
        return DualSystemInput(text=text, session_id=session_id)

    return _create
