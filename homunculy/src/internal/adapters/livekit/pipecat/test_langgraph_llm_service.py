from unittest.mock import AsyncMock

import pytest
from pipecat.frames.frames import (
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection

from internal.adapters.livekit.pipecat.langgraph_llm_service import LangGraphLLMService
from internal.domain.entities import AgentConfiguration, AgentPersonality, AgentProvider
from internal.domain.services import LLMService as DomainLLMService


@pytest.mark.asyncio
async def test_generate_response():
    llm = AsyncMock(spec=DomainLLMService)

    async def _stream(*args, **kwargs):
        yield "Hello"
        yield " World"

    llm.stream_chat.return_value = _stream()

    config = AgentConfiguration(
        provider=AgentProvider.LANGRAPH,
        model_name="gpt-4o-mini",
        personality=AgentPersonality(name="Default", description="Default assistant"),
        system_prompt="You are a helpful assistant.",
    )

    service = LangGraphLLMService(llm, config, "session-123")
    service.push_frame = AsyncMock()

    await service.process_frame(TextFrame(text="Hi"), FrameDirection.DOWNSTREAM)

    assert service.push_frame.call_count == 4

    args_list = service.push_frame.call_args_list
    assert isinstance(args_list[0][0][0], LLMFullResponseStartFrame)
    assert args_list[0][0][1] == FrameDirection.DOWNSTREAM

    assert isinstance(args_list[1][0][0], TextFrame)
    assert args_list[1][0][0].text == "Hello"
    assert args_list[1][0][1] == FrameDirection.DOWNSTREAM

    assert isinstance(args_list[2][0][0], TextFrame)
    assert args_list[2][0][0].text == " World"
    assert args_list[2][0][1] == FrameDirection.DOWNSTREAM

    assert isinstance(args_list[3][0][0], LLMFullResponseEndFrame)
    assert args_list[3][0][1] == FrameDirection.DOWNSTREAM
    assert isinstance(args_list[2][0][0], TextFrame)
    assert args_list[2][0][0].text == " World"
    assert isinstance(args_list[3][0][0], LLMFullResponseEndFrame)
