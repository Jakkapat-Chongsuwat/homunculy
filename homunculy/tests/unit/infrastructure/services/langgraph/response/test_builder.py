"""
Unit tests for ResponseBuilder.

Tests response construction and TTS audio generation.
"""

from unittest.mock import MagicMock

import pytest

from internal.domain.entities import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
    AgentStatus,
)
from internal.infrastructure.services.langgraph.response import (
    ResponseBuilder,
    create_response_builder,
)


class TestResponseBuilder:
    """Test ResponseBuilder functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AgentConfiguration(
            provider=AgentProvider.LANGRAPH,
            model_name="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
            personality=AgentPersonality(
                name="Test",
                description="Test agent",
                mood="happy",
            ),
        )

    def test_build_success(self, config):
        """Should build successful response."""
        builder = ResponseBuilder(storage_type="postgres")

        response = builder.build_success(
            configuration=config,
            thread_id="test-thread",
            response_text="Hello!",
            summary_used=True,
            checkpointer_name="AsyncPostgresSaver",
        )

        assert response.message == "Hello!"
        assert response.status == AgentStatus.COMPLETED
        assert response.confidence == 0.95
        assert response.metadata is not None
        assert response.metadata["thread_id"] == "test-thread"
        assert response.metadata["summary_used"] is True
        assert response.metadata["storage_type"] == "postgres"

    def test_build_success_with_audio(self, config):
        """Should include audio in metadata."""
        builder = ResponseBuilder()

        audio = {"data": "base64data", "format": "mp3"}
        response = builder.build_success(
            configuration=config,
            thread_id="test",
            response_text="Hi",
            summary_used=False,
            checkpointer_name="MemorySaver",
            audio_response=audio,
        )

        assert response.metadata is not None
        assert response.metadata["audio"] == audio

    def test_build_error(self):
        """Should build error response."""
        builder = ResponseBuilder()

        response = builder.build_error("Something went wrong")

        assert "Error:" in response.message
        assert response.status == AgentStatus.ERROR
        assert response.confidence == 0.0
        assert response.metadata is not None
        assert response.metadata["error"] == "Something went wrong"

    @pytest.mark.asyncio
    async def test_generate_audio_no_service(self):
        """Should return None when no TTS service."""
        builder = ResponseBuilder(tts_service=None)

        result = await builder.generate_audio("Hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_audio_short_text(self):
        """Should skip very short text."""
        mock_tts = MagicMock()
        builder = ResponseBuilder(tts_service=mock_tts)

        result = await builder.generate_audio("Hi")
        assert result is None


class TestResponseBuilderFactory:
    """Test factory function for ResponseBuilder."""

    def test_create_response_builder(self):
        """Factory should create builder."""
        builder = create_response_builder()
        assert isinstance(builder, ResponseBuilder)

    def test_create_response_builder_with_options(self):
        """Factory should accept options."""
        mock_tts = MagicMock()
        builder = create_response_builder(
            tts_service=mock_tts,
            storage_type="postgres",
        )
        # Verify it was created successfully
        assert isinstance(builder, ResponseBuilder)
