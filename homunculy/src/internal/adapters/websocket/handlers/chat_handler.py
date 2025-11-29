"""
WebSocket Chat Handler for Streaming TTS with Interruption Support.

This module provides real-time streaming chat with TTS audio chunks
and support for human-in-the-loop interruption (user can send new
messages while AI is responding, causing immediate cancellation).

Follows Clean Architecture by depending on use cases through interfaces.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from common.logger import get_logger
from internal.adapters.websocket.session_adapter import create_session_adapter
from internal.adapters.websocket.models import ConnectionStatus
from internal.usecases.streaming import StreamChatUseCaseImpl
from internal.infrastructure.container import get_stream_chat_usecase


logger = get_logger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    stream_chat_usecase: StreamChatUseCaseImpl = Depends(get_stream_chat_usecase),
):
    """
    WebSocket endpoint for real-time streaming chat with TTS and interruption support.

    **Human-in-the-Loop Interruption**:
    Users can send new messages while the AI is streaming a response.
    The AI will immediately stop (cancel ongoing text and audio streaming)
    and respond to the new message.

    Protocol Flow:
    1. Client connects and receives CONNECTION_STATUS
    2. Client sends ChatStreamRequest
    3. Server streams TEXT_CHUNK messages (AI response)
    4. Server streams AUDIO_CHUNK messages (TTS audio) if enabled
    5. If client sends new message during streaming:
       - Server sends INTERRUPTED message
       - Server cancels ongoing streams
       - Server immediately processes new message
    6. Server sends METADATA
    7. Server sends COMPLETE
    8. Connection remains open for next message

    Message Types:
    - Client -> Server: CHAT_REQUEST, PING
    - Server -> Client: TEXT_CHUNK, AUDIO_CHUNK, METADATA, COMPLETE,
                        ERROR, INTERRUPTED, PONG, CONNECTION_STATUS

    Args:
        websocket: WebSocket connection
        stream_chat_usecase: Use case for streaming chat (injected via DI)
    """
    await websocket.accept()

    # Send connection status
    status_msg = ConnectionStatus(
        status="connected",
        message="WebSocket connection established. Ready for chat requests with interrupt support.",
    )
    await websocket.send_json(status_msg.model_dump(mode="json"))
    logger.info("WebSocket connection established with interrupt support")

    # Create session adapter to handle concurrent operations and interrupts
    session_adapter = create_session_adapter(
        websocket=websocket,
        stream_chat_usecase=stream_chat_usecase,
    )

    try:
        # Start session (runs concurrent message receiver and processor)
        await session_adapter.start()

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error("WebSocket error", error=str(e), exc_info=True)
