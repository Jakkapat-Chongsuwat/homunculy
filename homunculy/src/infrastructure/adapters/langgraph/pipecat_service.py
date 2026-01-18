"""LangGraph Pipecat service - Bridges LangGraph with Pipecat."""

from collections.abc import AsyncIterator

from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    TextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService as PipecatLLMService

from common.logger import get_logger
from domain.entities import AgentConfiguration
from domain.interfaces import LLMPort

logger = get_logger(__name__)


class LangGraphPipecatService(PipecatLLMService):
    """Pipecat LLM service backed by LangGraph."""

    def __init__(
        self,
        llm: LLMPort,
        config: AgentConfiguration,
        session_id: str,
    ) -> None:
        super().__init__()
        self._llm = llm
        self._config = config
        self._session_id = session_id

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Process incoming frame."""
        await super().process_frame(frame, direction)
        if direction != FrameDirection.DOWNSTREAM:
            return await self._forward(frame, direction)
        await self._handle(frame, direction)

    async def _forward(self, frame: Frame, direction: FrameDirection) -> None:
        """Forward frame unchanged."""
        await self.push_frame(frame, direction)

    async def _handle(self, frame: Frame, direction: FrameDirection) -> None:
        """Handle downstream frame."""
        if isinstance(frame, TextFrame):
            return await self._respond(frame.text, direction)
        await self._forward(frame, direction)

    async def _respond(self, text: str, direction: FrameDirection) -> None:
        """Generate and stream response."""
        logger.info("Processing input", text=text[:50])
        await self._emit_start(direction)
        await self._stream_response(text, direction)
        await self._emit_end(direction)

    async def _emit_start(self, direction: FrameDirection) -> None:
        """Emit response start frame."""
        await self.push_frame(LLMFullResponseStartFrame(), direction)

    async def _emit_end(self, direction: FrameDirection) -> None:
        """Emit response end frame."""
        await self.push_frame(LLMFullResponseEndFrame(), direction)

    async def _stream_response(self, text: str, direction: FrameDirection) -> None:
        """Stream response chunks."""
        try:
            async for chunk in self._get_chunks(text):
                await self._emit_chunk(chunk, direction)
        except Exception as exc:
            logger.error("Stream failed", error=str(exc))

    def _get_chunks(self, text: str) -> AsyncIterator[str]:
        """Get response chunks from LLM."""
        return self._llm.stream_chat(self._config, text, self._context())

    async def _emit_chunk(self, chunk: str, direction: FrameDirection) -> None:
        """Emit text chunk frame."""
        if chunk:
            await self.push_frame(TextFrame(text=chunk), direction)

    def _context(self) -> dict:
        """Build context dict."""
        return {"session_id": self._session_id, "thread_id": self._session_id}
