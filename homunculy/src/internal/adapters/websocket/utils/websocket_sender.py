"""
WebSocket Sender - Send typed messages through WebSocket.

Single Responsibility: Format and send messages to client.
"""

import base64
from datetime import datetime, timezone
from typing import Optional

from fastapi import WebSocket

from internal.adapters.websocket.models.messages import (
    MessageType,
    ChatStreamResponse,
    AudioChunk,
    StreamMetadata,
    CompleteMessage,
    ErrorMessage,
    InterruptedMessage,
)


class WebSocketSender:
    """Send typed messages through WebSocket connection."""
    
    def __init__(self, websocket: WebSocket):
        self._ws = websocket
    
    async def send_pong(self) -> None:
        """Send PONG response."""
        await self._send({
            "type": MessageType.PONG,
            "timestamp": str(datetime.now(timezone.utc))
        })
    
    async def send_text_chunk(self, chunk: str, index: int, is_final: bool = False) -> None:
        """Send text chunk to client."""
        message = ChatStreamResponse(chunk=chunk, chunk_index=index, is_final=is_final)
        await self._send_model(message)
    
    async def send_audio_chunk(self, audio_bytes: bytes, index: int, is_final: bool = False) -> None:
        """Send audio chunk to client."""
        data = self._encode_audio(audio_bytes)
        message = AudioChunk(data=data, chunk_index=index, is_final=is_final, size_bytes=len(audio_bytes))
        await self._send_model(message)
    
    async def send_final_audio(self, index: int) -> None:
        """Send final audio marker."""
        message = AudioChunk(data="", chunk_index=index, is_final=True, size_bytes=0)
        await self._send_model(message)
    
    async def send_metadata(self, metadata: StreamMetadata) -> None:
        """Send stream metadata."""
        await self._send_model(metadata)
    
    async def send_complete(self, metadata: StreamMetadata) -> None:
        """Send completion message."""
        message = CompleteMessage(message="Stream completed successfully", metadata=metadata)
        await self._send_model(message)
    
    async def send_error(self, code: str, message: str) -> None:
        """Send error message."""
        error = ErrorMessage(code=code, message=message)
        await self._send_model(error)
    
    async def send_interrupted(self, text_chunk: int, audio_chunk: int) -> None:
        """Send interruption notification."""
        message = InterruptedMessage(
            reason="new_message",
            message="Stream interrupted - new message received",
            interrupted_at_text_chunk=text_chunk,
            interrupted_at_audio_chunk=audio_chunk,
        )
        await self._send_model(message)
    
    async def _send(self, data: dict) -> None:
        """Send raw dictionary as JSON."""
        await self._ws.send_json(data)
    
    async def _send_model(self, model) -> None:
        """Send Pydantic model as JSON."""
        await self._ws.send_json(model.model_dump(mode="json"))
    
    def _encode_audio(self, audio_bytes: bytes) -> str:
        """Encode audio bytes to base64."""
        return base64.b64encode(audio_bytes).decode("utf-8")


def create_sender(websocket: WebSocket) -> WebSocketSender:
    """Factory function for creating WebSocket sender."""
    return WebSocketSender(websocket)
