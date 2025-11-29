"""
Stream Chat Use Case - Orchestrate streaming chat with LLM and TTS.

Single Responsibility: Coordinate LLM streaming, text buffering, and TTS.
This is the main use case for real-time chat with optional audio streaming.
"""

import asyncio
from typing import Optional, Callable, Awaitable

from common.logger import get_logger
from internal.domain.entities import AgentConfiguration
from internal.domain.services import LLMService, TTSService
from internal.usecases.streaming.sentence_buffer import create_sentence_buffer
from internal.usecases.streaming.tts_streaming_usecase import (
    TTSStreamingUseCaseImpl,
    create_tts_streaming_usecase,
)


logger = get_logger(__name__)


class StreamChatUseCaseImpl:
    """
    Use case for streaming chat with LLM and optional TTS.

    Follows Clean Architecture:
    - Depends on domain service abstractions (LLMService, TTSService)
    - Contains application-level business logic
    - Protocol-agnostic (works with any delivery mechanism via callbacks)
    """

    def __init__(
        self,
        llm_service: LLMService,
        tts_service: Optional[TTSService],
    ) -> None:
        """
        Initialize stream chat use case.

        Args:
            llm_service: Domain LLM service abstraction
            tts_service: Domain TTS service abstraction (optional)
        """
        self._llm = llm_service
        self._tts = tts_service
        self._text_chunk_index = 0

    @property
    def text_chunk_index(self) -> int:
        """Get current text chunk index."""
        return self._text_chunk_index

    async def execute(
        self,
        message: str,
        configuration: AgentConfiguration,
        context: dict,
        stream_audio: bool,
        voice_id: Optional[str],
        on_text_chunk: Optional[Callable[[str, int, bool], Awaitable[None]]],
        on_audio_chunk: Optional[Callable[[bytes, int, bool], Awaitable[None]]],
    ) -> tuple[str, int, int]:
        """
        Execute streaming chat and return results.

        Args:
            message: User message to send
            configuration: Agent configuration
            context: Conversation context including user_id
            stream_audio: Whether to generate TTS audio
            voice_id: Voice ID for TTS
            on_text_chunk: Callback for text chunks (chunk, index, is_final)
            on_audio_chunk: Callback for audio chunks (bytes, index, is_final)

        Returns:
            Tuple of (full_text, text_chunks_count, audio_chunks_count)
        """
        self._reset_state()

        tts_usecase = self._create_tts_usecase(stream_audio, voice_id, on_audio_chunk)
        tts_task = self._start_tts_task(tts_usecase)

        try:
            full_text = await self._stream_llm(
                message, configuration, context, on_text_chunk, tts_usecase
            )
            await self._finish_tts(tts_usecase, tts_task)

            audio_chunks = tts_usecase.chunks_sent if tts_usecase else 0
            return full_text, self._text_chunk_index, audio_chunks

        finally:
            await self._cleanup_tts(tts_task)

    def _reset_state(self) -> None:
        """Reset use case state for new request."""
        self._text_chunk_index = 0

    def _create_tts_usecase(
        self,
        stream_audio: bool,
        voice_id: Optional[str],
        on_audio_chunk: Optional[Callable[[bytes, int, bool], Awaitable[None]]],
    ) -> Optional[TTSStreamingUseCaseImpl]:
        """Create TTS use case if needed."""
        if not stream_audio or not voice_id or not on_audio_chunk:
            return None
        return create_tts_streaming_usecase(self._tts, voice_id, on_audio_chunk)

    def _start_tts_task(
        self, usecase: Optional[TTSStreamingUseCaseImpl]
    ) -> Optional[asyncio.Task]:
        """Start TTS use case as background task."""
        if usecase is None:
            return None
        return asyncio.create_task(usecase.run())

    async def _stream_llm(
        self,
        message: str,
        configuration: AgentConfiguration,
        context: dict,
        on_text_chunk: Optional[Callable[[str, int, bool], Awaitable[None]]],
        tts_usecase: Optional[TTSStreamingUseCaseImpl],
    ) -> str:
        """Stream LLM response and process through TTS."""
        buffer = create_sentence_buffer()
        full_text = ""

        async for chunk in self._llm.stream_chat(configuration, message, context):
            full_text += chunk
            await self._process_chunk(chunk, buffer, on_text_chunk, tts_usecase)

        await self._flush_buffer(buffer, tts_usecase)
        return full_text

    async def _process_chunk(
        self,
        chunk: str,
        buffer,
        on_text_chunk: Optional[Callable[[str, int, bool], Awaitable[None]]],
        tts_usecase: Optional[TTSStreamingUseCaseImpl],
    ) -> None:
        """Process a single text chunk."""
        self._text_chunk_index += 1

        if on_text_chunk:
            await on_text_chunk(chunk, self._text_chunk_index, False)

        if tts_usecase:
            buffer.add(chunk)
            await self._queue_sentences(buffer, tts_usecase)

        await asyncio.sleep(0.001)

    async def _queue_sentences(
        self, buffer, tts_usecase: TTSStreamingUseCaseImpl
    ) -> None:
        """Extract and queue complete sentences for TTS."""
        while True:
            sentence = buffer.extract_sentence()
            if sentence is None:
                break
            await tts_usecase.queue_sentence(sentence)
            logger.debug("Queued for TTS", text=sentence[:50])

    async def _flush_buffer(
        self, buffer, tts_usecase: Optional[TTSStreamingUseCaseImpl]
    ) -> None:
        """Flush remaining buffer content to TTS."""
        if tts_usecase is None:
            return

        remaining = buffer.flush()
        if remaining:
            await tts_usecase.queue_sentence(remaining)

    async def _finish_tts(
        self,
        usecase: Optional[TTSStreamingUseCaseImpl],
        task: Optional[asyncio.Task],
    ) -> None:
        """Signal TTS use case to finish and wait for completion."""
        if usecase is None or task is None:
            return

        await usecase.finish()
        await task

    async def _cleanup_tts(self, task: Optional[asyncio.Task]) -> None:
        """Cancel TTS task if still running."""
        if task is None or task.done():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def create_stream_chat_usecase(
    llm_service: LLMService,
    tts_service: Optional[TTSService],
) -> StreamChatUseCaseImpl:
    """
    Factory function for creating stream chat use case.

    Args:
        llm_service: LLM service for chat
        tts_service: TTS service for audio (optional)

    Returns:
        StreamChatUseCaseImpl instance
    """
    return StreamChatUseCaseImpl(llm_service, tts_service)
