"""LangGraph adapter for Pipecat."""

from collections.abc import AsyncIterator

from common.logger import get_logger
from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService as PipecatLLMService

from internal.domain.entities import AgentConfiguration
from internal.domain.services import LLMService as DomainLLMService

logger = get_logger(__name__)


class LangGraphLLMService(PipecatLLMService):
    """Pipecat LLM service backed by the domain LLM port."""

    def __init__(
        self,
        llm_service: DomainLLMService,
        configuration: AgentConfiguration,
        session_id: str,
    ) -> None:
        super().__init__()
        self._llm_service = llm_service
        self._configuration = configuration
        self._session_id = session_id

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if direction != FrameDirection.DOWNSTREAM:
            return await self._forward(frame, direction)
        await self._handle_downstream(frame, direction)

    async def _forward(self, frame: Frame, direction: FrameDirection) -> None:
        await self.push_frame(frame, direction)

    async def _handle_downstream(self, frame: Frame, direction: FrameDirection) -> None:
        if isinstance(frame, TextFrame):
            return await self._respond(frame.text, direction)
        await self._forward(frame, direction)

    async def _respond(self, text: str, direction: FrameDirection) -> None:
        logger.info("Processing user input", text=text)
        await self._start(direction)
        await self._stream(text, direction)
        await self._end(direction)

    async def _start(self, direction: FrameDirection) -> None:
        await self.push_frame(LLMFullResponseStartFrame(), direction)

    async def _end(self, direction: FrameDirection) -> None:
        await self.push_frame(LLMFullResponseEndFrame(), direction)

    async def _stream(self, text: str, direction: FrameDirection) -> None:
        try:
            async for chunk in self._chunks(text):
                await self._emit_text(chunk, direction)
        except Exception as exc:
            _log_stream_error(exc)

    def _chunks(self, text: str) -> AsyncIterator[str]:
        return self._llm_service.stream_chat(self._configuration, text, self._context())

    async def _emit_text(self, chunk: str, direction: FrameDirection) -> None:
        if chunk:
            await self.push_frame(TextFrame(text=chunk), direction)

    def _context(self) -> dict:
        return {"session_id": self._session_id}


def _log_stream_error(exc: Exception) -> None:
    logger.error("LLM stream failed", error=str(exc))
