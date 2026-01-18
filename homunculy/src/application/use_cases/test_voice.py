"""Unit tests for Voice use case."""

from unittest.mock import AsyncMock

import pytest

from application.use_cases.voice import VoiceInput, VoiceOutput, VoiceUseCase
from domain.entities.agent import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
)


class TestVoiceInput:
    """Tests for VoiceInput DTO."""

    def test_create_input(self) -> None:
        config = _create_config()
        input_ = VoiceInput(
            audio=b"audio_data",
            config=config,
            thread_id="t1",
            voice_id="voice-1",
        )
        assert input_.audio == b"audio_data"
        assert input_.voice_id == "voice-1"


class TestVoiceOutput:
    """Tests for VoiceOutput DTO."""

    def test_create_output(self) -> None:
        output = VoiceOutput(
            audio=b"tts_audio",
            transcript="Hello",
            response_text="Hi!",
            thread_id="t1",
        )
        assert output.transcript == "Hello"
        assert output.response_text == "Hi!"


class TestVoiceUseCase:
    """Tests for VoiceUseCase."""

    @pytest.fixture
    def mock_stt(self) -> AsyncMock:
        stt = AsyncMock()
        stt.transcribe.return_value = "Hello"
        return stt

    @pytest.fixture
    def mock_llm(self) -> AsyncMock:
        llm = AsyncMock()
        llm.chat.return_value = AgentResponse(
            message="Response",
            confidence=0.95,
        )
        return llm

    @pytest.fixture
    def mock_tts(self) -> AsyncMock:
        tts = AsyncMock()
        tts.synthesize.return_value = b"audio_output"
        return tts

    @pytest.mark.asyncio
    async def test_execute_pipeline(
        self,
        mock_stt: AsyncMock,
        mock_llm: AsyncMock,
        mock_tts: AsyncMock,
    ) -> None:
        use_case = VoiceUseCase(mock_stt, mock_llm, mock_tts)
        input_ = VoiceInput(
            audio=b"input_audio",
            config=_create_config(),
            thread_id="t1",
            voice_id="v1",
        )
        output = await use_case.execute(input_)
        assert output.transcript == "Hello"
        assert output.response_text == "Response"
        assert output.audio == b"audio_output"

    @pytest.mark.asyncio
    async def test_stt_called_with_audio(
        self,
        mock_stt: AsyncMock,
        mock_llm: AsyncMock,
        mock_tts: AsyncMock,
    ) -> None:
        use_case = VoiceUseCase(mock_stt, mock_llm, mock_tts)
        input_ = VoiceInput(
            audio=b"test_audio",
            config=_create_config(),
            thread_id="t1",
            voice_id="v1",
        )
        await use_case.execute(input_)
        mock_stt.transcribe.assert_called_once_with(b"test_audio")

    @pytest.mark.asyncio
    async def test_tts_called_with_voice_id(
        self,
        mock_stt: AsyncMock,
        mock_llm: AsyncMock,
        mock_tts: AsyncMock,
    ) -> None:
        use_case = VoiceUseCase(mock_stt, mock_llm, mock_tts)
        input_ = VoiceInput(
            audio=b"audio",
            config=_create_config(),
            thread_id="t1",
            voice_id="voice-123",
        )
        await use_case.execute(input_)
        mock_tts.synthesize.assert_called_once_with("Response", "voice-123")


def _create_config() -> AgentConfiguration:
    """Create test configuration."""
    personality = AgentPersonality(name="Test", description="Test")
    return AgentConfiguration(
        provider=AgentProvider.LANGRAPH,
        model_name="gpt-4o",
        personality=personality,
    )
