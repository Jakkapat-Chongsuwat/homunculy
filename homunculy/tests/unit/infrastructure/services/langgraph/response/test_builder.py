"""
Unit tests for ResponseBuilder.

Tests response construction and TTS audio generation.
"""

import base64
from unittest.mock import AsyncMock, MagicMock, patch

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

    @pytest.mark.asyncio
    async def test_generate_audio_success(self):
        """Should generate audio and return proper response."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(return_value=b"fake_audio_bytes")

        builder = ResponseBuilder(tts_service=mock_tts)

        with patch(
            "internal.infrastructure.services.langgraph.response.builder.tts_settings"
        ) as mock_settings:
            mock_settings.default_voice_id = "test_voice"
            mock_settings.elevenlabs_model_id = "eleven_turbo"
            mock_settings.default_stability = 0.5
            mock_settings.default_similarity_boost = 0.75
            mock_settings.default_style = 0.0
            mock_settings.default_use_speaker_boost = True

            result = await builder.generate_audio("Hello, this is a test message!")

        assert result is not None
        assert result["format"] == "mp3"
        assert result["encoding"] == "base64"
        assert result["voice_id"] == "test_voice"
        assert result["size_bytes"] == len(b"fake_audio_bytes")
        # Verify base64 encoding
        assert result["data"] == base64.b64encode(b"fake_audio_bytes").decode("utf-8")

    @pytest.mark.asyncio
    async def test_generate_audio_handles_exception(self):
        """Should return None on TTS failure."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(side_effect=Exception("TTS API error"))

        builder = ResponseBuilder(tts_service=mock_tts)

        with patch(
            "internal.infrastructure.services.langgraph.response.builder.tts_settings"
        ) as mock_settings:
            mock_settings.default_voice_id = "test_voice"
            mock_settings.elevenlabs_model_id = "eleven_turbo"
            mock_settings.default_stability = 0.5
            mock_settings.default_similarity_boost = 0.75
            mock_settings.default_style = 0.0
            mock_settings.default_use_speaker_boost = True

            result = await builder.generate_audio("Hello, this is a test!")

        assert result is None

    @pytest.mark.asyncio
    async def test_generate_audio_cleans_tool_text(self):
        """Should clean tool-related text before TTS."""
        mock_tts = AsyncMock()
        mock_tts.synthesize = AsyncMock(return_value=b"audio")

        builder = ResponseBuilder(tts_service=mock_tts)

        with patch(
            "internal.infrastructure.services.langgraph.response.builder.tts_settings"
        ) as mock_settings:
            mock_settings.default_voice_id = "voice"
            mock_settings.elevenlabs_model_id = "model"
            mock_settings.default_stability = 0.5
            mock_settings.default_similarity_boost = 0.75
            mock_settings.default_style = 0.0
            mock_settings.default_use_speaker_boost = True

            await builder.generate_audio("Called tool: text_to_speech Hello world!")

        call_args = mock_tts.synthesize.call_args
        assert "Called tool:" not in call_args.kwargs["text"]
        assert "text_to_speech" not in call_args.kwargs["text"]

    def test_clean_text_for_tts(self):
        """Should remove tool-related prefixes from text."""
        text = "Called tool: text_to_speech Generate audio"
        expected_cleaned = "Generate audio"
        cleaned = text.replace("Called tool:", "").replace("text_to_speech", "").strip()
        assert cleaned == expected_cleaned

    def test_update_storage_type(self):
        """Should update storage type."""
        builder = ResponseBuilder(storage_type="memory")

        builder.update_storage_type("postgres")

        config = AgentConfiguration(
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
        response = builder.build_success(
            configuration=config,
            thread_id="test",
            response_text="test",
            summary_used=False,
            checkpointer_name="test",
        )
        assert response.metadata is not None
        assert response.metadata["storage_type"] == "postgres"


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
        assert isinstance(builder, ResponseBuilder)
