"""
End-to-End Tests using TestContainers.

Tests the full stack:
1. PostgreSQL + Migrations
2. Dual-System (Reflex + Cognition)
3. API endpoints

Run: pytest tests/e2e/ -v
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from domain.interfaces import DualSystemInput, DualSystemOutput


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def postgres_container():
    """Start PostgreSQL container for tests."""
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="module")
def db_url(postgres_container: PostgresContainer) -> str:
    """Get database URL from container."""
    return postgres_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql://"
    )


@pytest.fixture
async def checkpointer(db_url: str):
    """Create checkpointer connected to test database."""
    from infrastructure.persistence import CheckpointerFactory

    cp = await CheckpointerFactory.create_postgres(db_url)
    yield cp.checkpointer
    await cp.cleanup()


class TestDualSystemE2E:
    """End-to-end tests for Dual-System architecture."""

    @pytest_asyncio.fixture
    async def dual_system(self):
        """Create dual-system for testing."""
        from infrastructure.adapters.factory import (
            create_cognition,
            create_dual_system,
            create_emotion_detector,
            create_orchestrator,
            create_reflex,
        )

        orchestrator = create_orchestrator()
        reflex = create_reflex()
        cognition = create_cognition(orchestrator=orchestrator)
        emotion = create_emotion_detector()
        ds = create_dual_system(reflex, cognition, emotion)
        yield ds
        await orchestrator.close()

    @pytest.mark.asyncio
    async def test_reflex_handles_greeting(self, dual_system):
        """Reflex should handle greetings without cognition."""
        input_ = DualSystemInput(
            text="Hello!",
            session_id="test-session-001",
        )
        output = await dual_system.process(input_)

        assert output.response_type.value == "reflex"
        assert output.reflex is not None
        assert "Hi" in output.text or "Hello" in output.text

    @pytest.mark.asyncio
    async def test_reflex_handles_time_query(self, dual_system):
        """Reflex should handle simple time queries."""
        input_ = DualSystemInput(
            text="What time is it?",
            session_id="test-session-002",
        )
        output = await dual_system.process(input_)

        assert output.response_type.value == "reflex"
        assert ":" in output.text  # Time format

    @pytest.mark.asyncio
    async def test_cognition_handles_complex_query(self, dual_system):
        """Cognition should handle complex queries."""
        input_ = DualSystemInput(
            text="Explain the difference between REST and GraphQL APIs",
            session_id="test-session-003",
        )
        output = await dual_system.process(input_)

        assert output.response_type.value == "cognition"
        assert output.cognition is not None
        assert len(output.text) > 50  # Should have substantial response

    @pytest.mark.asyncio
    async def test_emotion_detection(self, dual_system):
        """Should detect emotional tone in input."""
        input_ = DualSystemInput(
            text="This is so frustrating!! It doesn't work!",
            session_id="test-session-004",
        )
        output = await dual_system.process(input_)

        assert output.emotion.value == "frustrated"

    @pytest.mark.asyncio
    async def test_streaming_response(self, dual_system):
        """Should stream responses progressively."""
        input_ = DualSystemInput(
            text="Tell me a short story",
            session_id="test-session-005",
        )
        chunks = []
        async for chunk in dual_system.stream(input_):
            chunks.append(chunk)

        assert len(chunks) >= 1
        assert all(isinstance(c, DualSystemOutput) for c in chunks)


class TestReflexLayerE2E:
    """End-to-end tests for Reflex layer specifically."""

    @pytest.fixture
    def reflex(self):
        """Create reflex adapter."""
        from infrastructure.adapters.factory import create_reflex

        return create_reflex()

    @pytest.mark.asyncio
    async def test_can_handle_greeting(self, reflex):
        """Should recognize greetings."""
        input_ = DualSystemInput(text="Hi there", session_id="test")
        assert reflex.can_handle(input_)

    @pytest.mark.asyncio
    async def test_can_handle_thanks(self, reflex):
        """Should recognize acknowledgments."""
        input_ = DualSystemInput(text="thanks", session_id="test")
        assert reflex.can_handle(input_)

    @pytest.mark.asyncio
    async def test_cannot_handle_complex(self, reflex):
        """Should not try to handle complex queries."""
        input_ = DualSystemInput(
            text="How do I implement a binary search tree?",
            session_id="test",
        )
        assert not reflex.can_handle(input_)

    @pytest.mark.asyncio
    async def test_personalized_greeting(self, reflex):
        """Should use name if available."""
        input_ = DualSystemInput(
            text="Hello",
            session_id="test",
            context={"user_name": "Alice"},
        )
        output = await reflex.respond(input_)
        assert "Alice" in output.text


class TestCognitionLayerE2E:
    """End-to-end tests for Cognition layer specifically."""

    @pytest_asyncio.fixture
    async def cognition(self):
        """Create cognition adapter with real orchestrator."""
        from infrastructure.adapters.factory import (
            create_cognition,
            create_orchestrator,
        )

        orchestrator = create_orchestrator()
        cog = create_cognition(orchestrator=orchestrator)
        yield cog
        await orchestrator.close()

    @pytest.mark.asyncio
    async def test_reason_returns_output(self, cognition):
        """Should return cognition output."""
        input_ = DualSystemInput(
            text="What is machine learning?",
            session_id="test-cog-001",
        )
        output = await cognition.reason(input_)

        assert output.text
        assert isinstance(output.text, str)


class TestEmotionDetectorE2E:
    """End-to-end tests for Emotion detector."""

    @pytest.fixture
    def emotion_detector(self):
        """Create emotion detector."""
        from infrastructure.adapters.factory import create_emotion_detector

        return create_emotion_detector()

    @pytest.mark.asyncio
    async def test_detects_frustration(self, emotion_detector):
        """Should detect frustration."""
        input_ = DualSystemInput(
            text="This stupid thing is broken!",
            session_id="test",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "frustrated"

    @pytest.mark.asyncio
    async def test_detects_urgency(self, emotion_detector):
        """Should detect urgency."""
        input_ = DualSystemInput(
            text="I need this ASAP, it's urgent!",
            session_id="test",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "urgent"

    @pytest.mark.asyncio
    async def test_detects_happiness(self, emotion_detector):
        """Should detect happiness."""
        input_ = DualSystemInput(
            text="Thank you so much! This is awesome!",
            session_id="test",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "happy"

    @pytest.mark.asyncio
    async def test_neutral_default(self, emotion_detector):
        """Should default to neutral."""
        input_ = DualSystemInput(
            text="What is the capital of France?",
            session_id="test",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "neutral"
