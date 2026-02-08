"""Dual-System Integration Tests.

Tests the Dual-System architecture layers:
- Reflex Layer: Fast pattern-matching responses
- Cognition Layer: LLM-powered reasoning (mocked)
- Emotion Detector: Emotion classification
- Dual-System Orchestrator: Layer coordination
"""

from __future__ import annotations

import pytest

from domain.interfaces import (
    DualSystemInput,
    DualSystemOutput,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
    ResponseType,
)

# =============================================================================
# Mock Orchestrator (replaces LLM)
# =============================================================================


class MockOrchestrator(OrchestratorPort):
    """Mock orchestrator for testing cognition without LLM."""

    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        """Return mock response based on input."""
        return OrchestrationOutput(
            message=f"Mock cognition response to: {input_.message[:50]}",
            tool_calls=None,
            metadata={"mock": True},
        )

    async def stream(self, input_: OrchestrationInput):
        """Stream mock response."""
        yield f"Mock streaming: {input_.message[:30]}"


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def reflex():
    """Create reflex adapter."""
    from infrastructure.adapters.factory import create_reflex

    return create_reflex()


@pytest.fixture
def emotion_detector():
    """Create emotion detector."""
    from infrastructure.adapters.factory import create_emotion_detector

    return create_emotion_detector()


@pytest.fixture
def cognition():
    """Create cognition adapter with mock orchestrator."""
    from infrastructure.adapters.factory import create_cognition

    return create_cognition(orchestrator=MockOrchestrator())


@pytest.fixture
def dual_system(reflex, cognition, emotion_detector):
    """Create full dual-system for testing."""
    from infrastructure.adapters.factory import create_dual_system

    return create_dual_system(
        reflex=reflex,
        cognition=cognition,
        emotion=emotion_detector,
    )


# =============================================================================
# Tests - Reflex Layer
# =============================================================================


class TestReflexLayer:
    """Reflex layer integration tests."""

    @pytest.mark.asyncio
    async def test_handles_greeting(self, reflex):
        """Reflex handles greetings."""
        input_ = DualSystemInput(text="Hello!", session_id="test-1")
        assert reflex.can_handle(input_)

        output = await reflex.respond(input_)
        assert "Hi" in output.text or "Hello" in output.text

    @pytest.mark.asyncio
    async def test_handles_thanks(self, reflex):
        """Reflex handles acknowledgments."""
        input_ = DualSystemInput(text="thanks", session_id="test-2")
        assert reflex.can_handle(input_)

    @pytest.mark.asyncio
    async def test_handles_time_query(self, reflex):
        """Reflex handles time queries."""
        input_ = DualSystemInput(text="What time is it?", session_id="test-3")
        if reflex.can_handle(input_):
            output = await reflex.respond(input_)
            assert ":" in output.text  # Time format

    @pytest.mark.asyncio
    async def test_cannot_handle_complex(self, reflex):
        """Reflex rejects complex queries."""
        input_ = DualSystemInput(
            text="Explain the difference between REST and GraphQL",
            session_id="test-4",
        )
        assert not reflex.can_handle(input_)

    @pytest.mark.asyncio
    async def test_personalized_greeting(self, reflex):
        """Reflex uses name from context."""
        input_ = DualSystemInput(
            text="Hello",
            session_id="test-5",
            context={"user_name": "Alice"},
        )
        if reflex.can_handle(input_):
            output = await reflex.respond(input_)
            assert "Alice" in output.text


# =============================================================================
# Tests - Cognition Layer
# =============================================================================


class TestCognitionLayer:
    """Cognition layer integration tests."""

    @pytest.mark.asyncio
    async def test_reason_returns_output(self, cognition):
        """Cognition returns output from orchestrator."""
        input_ = DualSystemInput(
            text="What is machine learning?",
            session_id="test-cog-1",
        )
        output = await cognition.reason(input_)

        assert output.text
        assert "Mock cognition" in output.text

    @pytest.mark.asyncio
    async def test_reason_handles_long_input(self, cognition):
        """Cognition handles long input."""
        long_text = "Explain in detail " + "a" * 200
        input_ = DualSystemInput(text=long_text, session_id="test-cog-2")
        output = await cognition.reason(input_)

        assert output.text


# =============================================================================
# Tests - Emotion Detector
# =============================================================================


class TestEmotionDetector:
    """Emotion detector integration tests."""

    @pytest.mark.asyncio
    async def test_detects_frustration(self, emotion_detector):
        """Detects frustration."""
        input_ = DualSystemInput(
            text="This stupid thing is broken!",
            session_id="test-em-1",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "frustrated"

    @pytest.mark.asyncio
    async def test_detects_urgency(self, emotion_detector):
        """Detects urgency."""
        input_ = DualSystemInput(
            text="I need this ASAP, it's urgent!",
            session_id="test-em-2",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "urgent"

    @pytest.mark.asyncio
    async def test_detects_happiness(self, emotion_detector):
        """Detects happiness."""
        input_ = DualSystemInput(
            text="Thank you so much! This is awesome!",
            session_id="test-em-3",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "happy"

    @pytest.mark.asyncio
    async def test_defaults_to_neutral(self, emotion_detector):
        """Defaults to neutral."""
        input_ = DualSystemInput(
            text="What is the capital of France?",
            session_id="test-em-4",
        )
        emotion = await emotion_detector.detect(input_)
        assert emotion.value == "neutral"


# =============================================================================
# Tests - Dual-System Orchestration
# =============================================================================


class TestDualSystem:
    """Dual-system orchestrator integration tests."""

    @pytest.mark.asyncio
    async def test_reflex_handles_greeting(self, dual_system):
        """Greeting routed to reflex."""
        input_ = DualSystemInput(text="Hello!", session_id="test-ds-1")
        output = await dual_system.process(input_)

        assert output.response_type == ResponseType.REFLEX
        assert output.reflex is not None

    @pytest.mark.asyncio
    async def test_cognition_handles_complex(self, dual_system):
        """Complex query routed to cognition."""
        input_ = DualSystemInput(
            text="Explain the difference between REST and GraphQL APIs",
            session_id="test-ds-2",
        )
        output = await dual_system.process(input_)

        assert output.response_type == ResponseType.COGNITION
        assert output.cognition is not None
        assert "Mock cognition" in output.text

    @pytest.mark.asyncio
    async def test_emotion_detected(self, dual_system):
        """Emotion detected on all inputs."""
        input_ = DualSystemInput(
            text="This is so frustrating!!",
            session_id="test-ds-3",
        )
        output = await dual_system.process(input_)

        assert output.emotion is not None
        assert output.emotion.value == "frustrated"

    @pytest.mark.asyncio
    async def test_streaming(self, dual_system):
        """Streaming returns chunks."""
        input_ = DualSystemInput(
            text="Tell me a story",
            session_id="test-ds-4",
        )
        chunks = []
        async for chunk in dual_system.stream(input_):
            chunks.append(chunk)

        assert len(chunks) >= 1
        assert all(isinstance(c, DualSystemOutput) for c in chunks)
