"""
WebSocket Session Manager - Adapter for WebSocket chat sessions.

This is an adapter-layer component that:
- Handles WebSocket protocol specifics (receive, send, parse)
- Delegates business logic to use cases
- Manages concurrent operations and interrupts
"""

import asyncio
from typing import Optional

from fastapi import WebSocket

from common.logger import get_logger
from internal.adapters.websocket.models.messages import (
    ChatStreamRequest,
    StreamMetadata,
)
from internal.adapters.websocket.utils import (
    ParseError,
    build_context,
    create_sender,
    map_configuration,
    parse_message,
)
from internal.usecases.streaming import StreamChatUseCaseImpl


logger = get_logger(__name__)


class WebSocketSessionAdapter:
    """
    WebSocket session adapter with interrupt support.

    Follows Clean Architecture:
    - Adapter layer: handles protocol-specific concerns
    - Delegates to use case for business logic
    - Uses callbacks to bridge use case output to WebSocket
    """

    def __init__(
        self,
        websocket: WebSocket,
        stream_chat_usecase: StreamChatUseCaseImpl,
    ) -> None:
        """
        Initialize session adapter.

        Args:
            websocket: FastAPI WebSocket connection
            stream_chat_usecase: Use case for streaming chat
        """
        self._websocket = websocket
        self._stream_chat = stream_chat_usecase
        self._sender = create_sender(websocket)
        self._queue: asyncio.Queue = asyncio.Queue()
        self._active_task: Optional[asyncio.Task] = None
        self._audio_chunk_index = 0

    async def start(self) -> None:
        """Start session with concurrent receive and process."""
        try:
            await self._run_concurrent()
        finally:
            await self._cleanup()

    async def _run_concurrent(self) -> None:
        """Run receiver and processor concurrently."""
        await asyncio.gather(
            self._receive_loop(),
            self._process_loop(),
        )

    async def _receive_loop(self) -> None:
        """Continuously receive and queue messages."""
        while True:
            message = await self._receive_message()
            if message is None:
                break
            await self._queue.put(message)

    async def _receive_message(self) -> Optional[str]:
        """Receive single message from WebSocket."""
        try:
            return await self._websocket.receive_text()
        except Exception as e:
            logger.error("Receive error", error=str(e))
            await self._queue.put(None)
            return None

    async def _process_loop(self) -> None:
        """Process messages from queue."""
        while True:
            message = await self._queue.get()
            if message is None:
                break
            await self._handle_message(message)

    async def _handle_message(self, raw: str) -> None:
        """Parse and route a message."""
        parsed, error = parse_message(raw)

        if error:
            await self._handle_error(error)
        elif parsed == "ping":
            await self._handle_ping()
        elif isinstance(parsed, ChatStreamRequest):
            await self._handle_chat(parsed)

    async def _handle_error(self, error: ParseError) -> None:
        """Handle parse error."""
        await self._sender.send_error(error.code, error.message)

    async def _handle_ping(self) -> None:
        """Handle ping message."""
        await self._sender.send_pong()

    async def _handle_chat(self, request: ChatStreamRequest) -> None:
        """Handle chat request with interrupt support."""
        await self._interrupt_if_active()
        self._active_task = asyncio.create_task(self._run_chat(request))

    async def _run_chat(self, request: ChatStreamRequest) -> None:
        """Run chat with error handling."""
        try:
            configuration = map_configuration(request)
            context = build_context(request)

            self._log_start(request)

            full_text, text_chunks, audio_chunks = await self._stream_chat.execute(
                message=request.message,
                configuration=configuration,
                context=context,
                stream_audio=request.stream_audio,
                voice_id=request.voice_id,
                on_text_chunk=self._on_text_chunk,
                on_audio_chunk=self._on_audio_chunk,
            )

            await self._send_completion(
                request, configuration, text_chunks, audio_chunks, full_text
            )

        except asyncio.CancelledError:
            self._log_interrupted()
            raise
        except Exception as e:
            await self._handle_chat_error(e)

    async def _on_text_chunk(self, chunk: str, index: int, is_final: bool) -> None:
        """Callback for text chunks from use case."""
        await self._sender.send_text_chunk(chunk, index, is_final)

    async def _on_audio_chunk(
        self, audio_bytes: bytes, index: int, is_final: bool
    ) -> None:
        """Callback for audio chunks from use case."""
        self._audio_chunk_index = index
        await self._sender.send_audio_chunk(audio_bytes, index, is_final)

    async def _send_completion(
        self,
        request: ChatStreamRequest,
        configuration,
        text_chunks: int,
        audio_chunks: int,
        full_text: str,
    ) -> None:
        """Send completion messages."""
        await self._send_final_markers(text_chunks, audio_chunks)

        metadata = self._build_metadata(
            request, configuration, text_chunks, audio_chunks
        )
        self._log_completion(request, full_text, audio_chunks)

        await self._sender.send_metadata(metadata)
        await self._sender.send_complete(metadata)

    async def _send_final_markers(self, text_chunks: int, audio_chunks: int) -> None:
        """Send final text and audio markers."""
        await self._sender.send_text_chunk("", text_chunks + 1, is_final=True)

        if audio_chunks > 0:
            await self._sender.send_final_audio(audio_chunks + 1)

    def _build_metadata(
        self,
        request: ChatStreamRequest,
        configuration,
        text_chunks: int,
        audio_chunks: int,
    ) -> StreamMetadata:
        """Build stream metadata."""
        return StreamMetadata(
            model_used=configuration.model_name,
            tokens_used=None,
            execution_time_ms=None,
            tools_called=[],
            thread_id=request.context.get("thread_id"),
            voice_id=request.voice_id if request.stream_audio else None,
            total_text_chunks=text_chunks,
            total_audio_chunks=audio_chunks,
        )

    async def _interrupt_if_active(self) -> None:
        """Interrupt active stream if exists."""
        if not self._is_active():
            return

        logger.info("Interrupting active stream")
        await self._cancel_active()
        await self._send_interrupted()

    def _is_active(self) -> bool:
        """Check if there's an active task."""
        return self._active_task is not None and not self._active_task.done()

    async def _cancel_active(self) -> None:
        """Cancel the active task."""
        self._active_task.cancel()

    async def _send_interrupted(self) -> None:
        """Send interruption notification."""
        text_index = self._stream_chat.text_chunk_index
        await self._sender.send_interrupted(text_index, self._audio_chunk_index)
        self._audio_chunk_index = 0

    async def _handle_chat_error(self, error: Exception) -> None:
        """Handle chat processing error."""
        logger.error("Chat error", error=str(error), exc_info=True)
        await self._sender.send_error("CHAT_ERROR", f"Chat failed: {str(error)}")

    def _log_start(self, request: ChatStreamRequest) -> None:
        """Log stream start."""
        logger.info(
            "Processing streaming chat",
            user_id=request.user_id,
            stream_audio=request.stream_audio,
            voice_id=request.voice_id,
        )

    def _log_completion(
        self,
        request: ChatStreamRequest,
        full_text: str,
        audio_chunks: int,
    ) -> None:
        """Log stream completion."""
        logger.info(
            "Streaming completed",
            user_id=request.user_id,
            audio_chunks=audio_chunks,
            total_text_length=len(full_text),
        )

    def _log_interrupted(self) -> None:
        """Log interruption event."""
        logger.info("Stream cancelled", checkpoint_preserved=True)

    async def _cleanup(self) -> None:
        """Clean up session resources."""
        logger.info("Cleaning up session")
        await self._cancel_if_active()
        self._clear_queue()

    async def _cancel_if_active(self) -> None:
        """Cancel active task if exists."""
        if not self._is_active():
            return

        self._active_task.cancel()
        try:
            await self._active_task
        except asyncio.CancelledError:
            pass

    def _clear_queue(self) -> None:
        """Clear remaining queue items."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break


def create_session_adapter(
    websocket: WebSocket,
    stream_chat_usecase: StreamChatUseCaseImpl,
) -> WebSocketSessionAdapter:
    """
    Factory function for creating WebSocket session adapter.

    Args:
        websocket: FastAPI WebSocket connection
        stream_chat_usecase: Use case for streaming chat

    Returns:
        WebSocketSessionAdapter instance
    """
    return WebSocketSessionAdapter(websocket, stream_chat_usecase)
