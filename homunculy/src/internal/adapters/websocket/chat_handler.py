"""
WebSocket Chat Handler for Streaming TTS.

This module provides real-time streaming chat with TTS audio chunks.
Follows Clean Architecture by depending on domain services through interfaces.
"""

import json
import base64
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from common.logger import get_logger
from settings.tts import tts_settings
from internal.adapters.websocket.models.messages import (
    MessageType,
    ChatStreamRequest,
    ChatStreamResponse,
    AudioChunk,
    StreamMetadata,
    CompleteMessage,
    ErrorMessage,
    ConnectionStatus,
)
from internal.domain.entities import AgentProvider, AgentPersonality, AgentConfiguration
from internal.domain.services import LLMService, TTSService
from internal.infrastructure.container import get_llm_service, get_tts_service


logger = get_logger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    llm_service: LLMService = Depends(get_llm_service),
    tts_service: Optional[TTSService] = Depends(get_tts_service),
):
    """
    WebSocket endpoint for real-time streaming chat with TTS.
    
    Protocol Flow:
    1. Client connects and receives CONNECTION_STATUS
    2. Client sends ChatStreamRequest
    3. Server streams TEXT_CHUNK messages (AI response)
    4. Server streams AUDIO_CHUNK messages (TTS audio) if enabled
    5. Server sends METADATA
    6. Server sends COMPLETE
    7. Connection remains open for next message
    
    Message Types:
    - Client -> Server: CHAT_REQUEST, PING
    - Server -> Client: TEXT_CHUNK, AUDIO_CHUNK, METADATA, COMPLETE, ERROR, PONG, CONNECTION_STATUS
    
    Args:
        websocket: WebSocket connection
        llm_service: LLM service for agent execution (injected)
        tts_service: TTS service for audio streaming (injected, optional)
    """
    await websocket.accept()
    
    # Send connection status
    status_msg = ConnectionStatus(
        status="connected",
        message="WebSocket connection established. Ready for chat requests."
    )
    await websocket.send_json(status_msg.model_dump(mode="json"))
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                # Handle ping
                if message_type == MessageType.PING:
                    await websocket.send_json({"type": MessageType.PONG, "timestamp": str(datetime.now(timezone.utc))})
                    continue
                
                # Handle chat request
                if message_type == MessageType.CHAT_REQUEST:
                    request = ChatStreamRequest(**message_data)
                    await handle_chat_stream(websocket, request, llm_service, tts_service)
                else:
                    error_msg = ErrorMessage(
                        code="INVALID_MESSAGE_TYPE",
                        message=f"Unknown message type: {message_type}",
                    )
                    await websocket.send_json(error_msg.model_dump(mode="json"))
                    
            except json.JSONDecodeError as e:
                error_msg = ErrorMessage(
                    code="INVALID_JSON",
                    message=f"Invalid JSON: {str(e)}",
                )
                await websocket.send_json(error_msg.model_dump(mode="json"))
                
            except Exception as e:
                logger.error("Error processing message", error=str(e), exc_info=True)
                error_msg = ErrorMessage(
                    code="PROCESSING_ERROR",
                    message=f"Error processing message: {str(e)}",
                )
                await websocket.send_json(error_msg.model_dump(mode="json"))
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error("WebSocket error", error=str(e), exc_info=True)
        try:
            error_msg = ErrorMessage(
                code="INTERNAL_ERROR",
                message=f"Internal server error: {str(e)}",
            )
            await websocket.send_json(error_msg.model_dump(mode="json"))
        except:
            pass  # Connection might be closed


async def handle_chat_stream(
    websocket: WebSocket,
    request: ChatStreamRequest,
    llm_service: LLMService,
    tts_service: Optional[TTSService],
):
    """
    Handle streaming chat request with optional TTS.
    
    Streams both text and audio chunks in real-time.
    
    Args:
        websocket: WebSocket connection
        request: Chat stream request
        llm_service: LLM service for agent execution
        tts_service: TTS service for audio streaming (optional)
    """
    try:
        # Map request to domain entities (following HTTP adapter pattern)
        personality = AgentPersonality(
            name=request.configuration.personality.name,
            description=request.configuration.personality.description,
            traits=request.configuration.personality.traits,
            mood=request.configuration.personality.mood,
        )
        
        try:
            provider = AgentProvider(request.configuration.provider)
        except ValueError:
            provider = AgentProvider.LANGRAPH
        
        configuration = AgentConfiguration(
            provider=provider,
            model_name=request.configuration.model_name,
            personality=personality,
            system_prompt=request.configuration.system_prompt,
            temperature=request.configuration.temperature,
            max_tokens=request.configuration.max_tokens,
        )
        
        # Add user_id to context for conversation isolation
        context = request.context.copy()
        context["user_id"] = request.user_id
        context["include_audio"] = False  # Disable built-in audio (we'll stream it separately)
        
        logger.info(
            "Processing streaming chat request",
            user_id=request.user_id,
            stream_audio=request.stream_audio,
            voice_id=request.voice_id
        )
        
        # Execute chat
        response = await llm_service.chat(configuration, request.message, context)
        
        # Stream text chunks (simulating character-by-character streaming)
        # In a real implementation, you'd stream from the LLM directly
        text = response.message
        chunk_size = 10  # Characters per chunk
        text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        for idx, chunk in enumerate(text_chunks):
            chunk_msg = ChatStreamResponse(
                chunk=chunk,
                chunk_index=idx,
                is_final=(idx == len(text_chunks) - 1)
            )
            await websocket.send_json(chunk_msg.model_dump(mode="json"))
        
        logger.info(
            "Text streaming completed",
            user_id=request.user_id,
            chunks=len(text_chunks),
            text_length=len(text)
        )
        
        # Stream audio if enabled and TTS service available
        audio_chunks_sent = 0
        if request.stream_audio and tts_service:
            try:
                logger.info("Starting audio streaming", voice_id=request.voice_id)
                
                audio_chunk_index = 0
                async for audio_chunk in tts_service.stream(
                    text=text,
                    voice_id=request.voice_id,
                    model_id=tts_settings.elevenlabs_streaming_model_id,
                ):
                    # Encode audio chunk to base64
                    audio_b64 = base64.b64encode(audio_chunk).decode("utf-8")
                    
                    audio_msg = AudioChunk(
                        data=audio_b64,
                        chunk_index=audio_chunk_index,
                        is_final=False,  # We don't know if it's final yet
                        size_bytes=len(audio_chunk)
                    )
                    await websocket.send_json(audio_msg.model_dump(mode="json"))
                    audio_chunk_index += 1
                    audio_chunks_sent += 1
                
                # Send final audio chunk marker
                if audio_chunks_sent > 0:
                    final_audio_msg = AudioChunk(
                        data="",
                        chunk_index=audio_chunk_index,
                        is_final=True,
                        size_bytes=0
                    )
                    await websocket.send_json(final_audio_msg.model_dump(mode="json"))
                
                logger.info(
                    "Audio streaming completed",
                    chunks=audio_chunks_sent,
                    voice_id=request.voice_id
                )
                
            except Exception as e:
                logger.error("Audio streaming failed", error=str(e), exc_info=True)
                error_msg = ErrorMessage(
                    code="AUDIO_STREAMING_ERROR",
                    message=f"Failed to stream audio: {str(e)}",
                )
                await websocket.send_json(error_msg.model_dump(mode="json"))
        
        # Send metadata
        metadata_dict = response.metadata or {}
        metadata = StreamMetadata(
            model_used=metadata_dict.get("model_used"),
            tokens_used=metadata_dict.get("tokens_used"),
            execution_time_ms=metadata_dict.get("execution_time_ms"),
            tools_called=metadata_dict.get("tools_called", []),
            thread_id=metadata_dict.get("thread_id"),
            voice_id=request.voice_id if request.stream_audio else None,
            total_text_chunks=len(text_chunks),
            total_audio_chunks=audio_chunks_sent,
        )
        await websocket.send_json(metadata.model_dump(mode="json"))
        
        # Send completion
        complete_msg = CompleteMessage(
            message="Stream completed successfully",
            metadata=metadata
        )
        await websocket.send_json(complete_msg.model_dump(mode="json"))
        
        logger.info(
            "Streaming session completed",
            user_id=request.user_id,
            text_chunks=len(text_chunks),
            audio_chunks=audio_chunks_sent
        )
        
    except Exception as e:
        logger.error("Chat streaming failed", error=str(e), exc_info=True)
        error_msg = ErrorMessage(
            code="CHAT_STREAMING_ERROR",
            message=f"Chat streaming failed: {str(e)}",
        )
        await websocket.send_json(error_msg.model_dump(mode="json"))
