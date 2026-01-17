"""Unit tests for Chat use case."""

from unittest.mock import AsyncMock

import pytest
from domain.entities.agent import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
)

from application.use_cases.chat import ChatInput, ChatOutput, ChatUseCase


class TestChatInput:
    """Tests for ChatInput DTO."""

    def test_create_input(self) -> None:
        config = _create_config()
        input_ = ChatInput(
            message="Hello",
            config=config,
            thread_id="t1",
        )
        assert input_.message == "Hello"
        assert input_.thread_id == "t1"

    def test_input_with_context(self) -> None:
        config = _create_config()
        input_ = ChatInput(
            message="Hi",
            config=config,
            thread_id="t1",
            context={"key": "value"},
        )
        assert input_.context == {"key": "value"}


class TestChatOutput:
    """Tests for ChatOutput DTO."""

    def test_create_output(self) -> None:
        resp = AgentResponse(message="Hello!", confidence=0.9)
        output = ChatOutput(response=resp, thread_id="t1")
        assert output.response.message == "Hello!"
        assert output.thread_id == "t1"


class TestChatUseCase:
    """Tests for ChatUseCase."""

    @pytest.fixture
    def mock_llm(self) -> AsyncMock:
        llm = AsyncMock()
        llm.chat.return_value = AgentResponse(
            message="Response",
            confidence=0.95,
        )
        return llm

    @pytest.mark.asyncio
    async def test_execute(self, mock_llm: AsyncMock) -> None:
        use_case = ChatUseCase(mock_llm)
        input_ = ChatInput(
            message="Hello",
            config=_create_config(),
            thread_id="t1",
        )
        output = await use_case.execute(input_)
        assert output.response.message == "Response"
        assert output.thread_id == "t1"

    @pytest.mark.asyncio
    async def test_execute_calls_llm(self, mock_llm: AsyncMock) -> None:
        use_case = ChatUseCase(mock_llm)
        input_ = ChatInput(
            message="Test",
            config=_create_config(),
            thread_id="t2",
        )
        await use_case.execute(input_)
        mock_llm.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_includes_thread_id(self, mock_llm: AsyncMock) -> None:
        use_case = ChatUseCase(mock_llm)
        input_ = ChatInput(
            message="Hi",
            config=_create_config(),
            thread_id="t3",
        )
        await use_case.execute(input_)
        _, _, context = mock_llm.chat.call_args[0]
        assert context["thread_id"] == "t3"


def _create_config() -> AgentConfiguration:
    """Create test configuration."""
    personality = AgentPersonality(name="Test", description="Test agent")
    return AgentConfiguration(
        provider=AgentProvider.LANGRAPH,
        model_name="gpt-4o",
        personality=personality,
    )
