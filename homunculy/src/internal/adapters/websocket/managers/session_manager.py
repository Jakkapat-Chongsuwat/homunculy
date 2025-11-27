"""
WebSocket Session Manager for Interruptible Streaming.

Manages WebSocket chat sessions with support for interrupting ongoing
streams when new messages arrive (human-in-the-loop pattern).

Follows Clean Architecture by delegating business logic to domain services
while handling WebSocket protocol and concurrent streaming management.
"""

import asyncio
import json
import base64
from typing import Optional
from datetime import datetime, timezone

from fastapi import WebSocket
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
    InterruptedMessage,
)
from internal.domain.entities import AgentProvider, AgentPersonality, AgentConfiguration
from internal.domain.services import LLMService, TTSService


logger = get_logger(__name__)


class WebSocketSessionManager:
    """
    Manages a single WebSocket chat session with interrupt support.
    
    Features:
    - Concurrent message receiving and response streaming
    - Automatic interruption of active streams when new messages arrive
    - Graceful cleanup and resource management
    - Clean separation between protocol handling and business logic
    
    Architecture:
    - Adapter layer component (handles WebSocket protocol specifics)
    - Delegates business logic to Domain services (LLMService, TTSService)
    - Maintains session state (active task, message queue, streaming counters)
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        llm_service: LLMService,
        tts_service: Optional[TTSService],
    ):
        """
        Initialize WebSocket session manager.
        
        Args:
            websocket: WebSocket connection
            llm_service: LLM service for agent execution
            tts_service: TTS service for audio streaming (optional)
        """
        self.websocket = websocket
        self.llm_service = llm_service
        self.tts_service = tts_service
        
        # Session state
        self.active_task: Optional[asyncio.Task] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_streaming = False
        
        # Streaming counters (for interruption context)
        self.current_text_chunk_index = 0
        self.current_audio_chunk_index = 0
    
    async def start(self):
        """
        Start the session with concurrent message receiving and processing.
        
        Runs two concurrent tasks:
        1. Message receiver: Continuously listens for incoming WebSocket messages
        2. Message processor: Processes messages from queue, handles interruptions
        
        Raises:
            WebSocketDisconnect: When client disconnects
            Exception: For other WebSocket errors
        """
        try:
            # Run receiver and processor concurrently
            await asyncio.gather(
                self._receive_messages(),
                self._process_messages(),
            )
        finally:
            # Cleanup on disconnect
            await self._cleanup()
    
    async def _receive_messages(self):
        """
        Continuously receive messages from WebSocket and queue them.
        
        This runs concurrently with message processing, allowing for
        real-time interruption when new messages arrive during streaming.
        """
        while True:
            try:
                data = await self.websocket.receive_text()
                await self.message_queue.put(data)
                
            except Exception as e:
                logger.error("Error receiving message", error=str(e))
                # Put error marker in queue to trigger graceful shutdown
                await self.message_queue.put(None)
                break
    
    async def _process_messages(self):
        """
        Process messages from queue with interrupt support.
        
        When a new message arrives while streaming is active:
        1. Cancel the active streaming task
        2. Send INTERRUPTED notification to client
        3. Start processing the new message immediately
        
        This enables real-time human-in-the-loop conversation flow.
        """
        while True:
            # Get next message from queue
            message_data = await self.message_queue.get()
            
            # None indicates connection closed or error
            if message_data is None:
                break
            
            try:
                # Parse message
                message = json.loads(message_data)
                message_type = message.get("type")
                
                # Handle PING
                if message_type == MessageType.PING:
                    await self._handle_ping()
                    continue
                
                # Handle CHAT_REQUEST
                if message_type == MessageType.CHAT_REQUEST:
                    # Cancel active streaming if exists
                    if self.active_task and not self.active_task.done():
                        logger.info("New message received while streaming - interrupting")
                        await self._interrupt_active_stream()
                    
                    # Parse request
                    request = ChatStreamRequest(**message)
                    
                    # Start new streaming task in background (don't await)
                    # This allows us to immediately receive next message for interruption
                    self.active_task = asyncio.create_task(
                        self._handle_chat_stream(request)
                    )
                    
                else:
                    # Unknown message type
                    error_msg = ErrorMessage(
                        code="INVALID_MESSAGE_TYPE",
                        message=f"Unknown message type: {message_type}",
                    )
                    await self.websocket.send_json(error_msg.model_dump(mode="json"))
                    
            except json.JSONDecodeError as e:
                error_msg = ErrorMessage(
                    code="INVALID_JSON",
                    message=f"Invalid JSON: {str(e)}",
                )
                await self.websocket.send_json(error_msg.model_dump(mode="json"))
                
            except Exception as e:
                logger.error("Error processing message", error=str(e), exc_info=True)
                error_msg = ErrorMessage(
                    code="PROCESSING_ERROR",
                    message=f"Error processing message: {str(e)}",
                )
                await self.websocket.send_json(error_msg.model_dump(mode="json"))
    
    async def _interrupt_active_stream(self):
        """
        Interrupt the currently active streaming task.
        
        Cancels the task and sends INTERRUPTED notification to client
        with context about where the interruption occurred.
        """
        if not self.active_task or self.active_task.done():
            return
        
        logger.info(
            "Interrupting active stream",
            text_chunk=self.current_text_chunk_index,
            audio_chunk=self.current_audio_chunk_index,
        )
        
        # Cancel the active task
        self.active_task.cancel()
        
        # Send interruption notification
        interrupted_msg = InterruptedMessage(
            reason="new_message",
            message="Stream interrupted - new message received",
            interrupted_at_text_chunk=self.current_text_chunk_index,
            interrupted_at_audio_chunk=self.current_audio_chunk_index,
        )
        
        try:
            await self.websocket.send_json(interrupted_msg.model_dump(mode="json"))
        except Exception as e:
            logger.error("Failed to send interruption notification", error=str(e))
        
        # Reset counters
        self.current_text_chunk_index = 0
        self.current_audio_chunk_index = 0
        self.is_streaming = False
    
    async def _handle_ping(self):
        """Handle PING message by responding with PONG."""
        await self.websocket.send_json({
            "type": MessageType.PONG,
            "timestamp": str(datetime.now(timezone.utc))
        })
    
    async def _handle_chat_stream(self, request: ChatStreamRequest):
        """
        Handle streaming chat request with real-time LLM → TTS pipeline.
        
        Streams text from LLM and immediately sends complete sentences to TTS
        for real-time audio generation. Audio starts playing while LLM is still
        generating text.
        
        Args:
            request: Chat stream request with configuration
            
        Raises:
            asyncio.CancelledError: When interrupted by new message
        """
        try:
            self.is_streaming = True
            self.current_text_chunk_index = 0
            self.current_audio_chunk_index = 0
            
            # Map request to domain entities
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
            
            # Add context for conversation isolation
            context = request.context.copy()
            context["user_id"] = request.user_id
            context["include_audio"] = False
            
            logger.info(
                "Processing streaming chat request",
                user_id=request.user_id,
                stream_audio=request.stream_audio,
                voice_id=request.voice_id,
                use_llm_streaming=True,
                realtime_tts=request.stream_audio and self.tts_service is not None
            )
            
            # Queue for sentences ready for TTS
            sentence_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
            audio_chunks_sent = 0
            
            async def tts_worker():
                """Worker that converts sentences to audio in real-time."""
                nonlocal audio_chunks_sent
                
                if not self.tts_service or not request.stream_audio:
                    return
                
                while True:
                    sentence = await sentence_queue.get()
                    if sentence is None:  # End signal
                        break
                    
                    if not sentence.strip():
                        continue
                    
                    try:
                        logger.debug("TTS processing sentence", text=sentence[:50])
                        
                        async for audio_chunk in self.tts_service.stream(
                            text=sentence,
                            voice_id=request.voice_id,
                            model_id=tts_settings.elevenlabs_streaming_model_id,
                        ):
                            self.current_audio_chunk_index += 1
                            
                            audio_b64 = base64.b64encode(audio_chunk).decode("utf-8")
                            audio_msg = AudioChunk(
                                data=audio_b64,
                                chunk_index=self.current_audio_chunk_index,
                                is_final=False,
                                size_bytes=len(audio_chunk)
                            )
                            await self.websocket.send_json(audio_msg.model_dump(mode="json"))
                            audio_chunks_sent += 1
                            
                            await asyncio.sleep(0.001)  # Yield for interruption
                            
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        logger.error("TTS error for sentence", error=str(e))
            
            # Start TTS worker if audio streaming is enabled
            tts_task = None
            if request.stream_audio and self.tts_service:
                tts_task = asyncio.create_task(tts_worker())
            
            try:
                # Stream LLM and accumulate sentences for TTS
                full_text = ""
                sentence_buffer = ""
                sentence_delimiters = {'.', '!', '?', '。', '！', '？', '\n'}
                
                async for text_chunk in self.llm_service.stream_chat(configuration, request.message, context):
                    self.current_text_chunk_index += 1
                    full_text += text_chunk
                    sentence_buffer += text_chunk
                    
                    # Send text chunk to client immediately
                    chunk_msg = ChatStreamResponse(
                        chunk=text_chunk,
                        chunk_index=self.current_text_chunk_index,
                        is_final=False
                    )
                    await self.websocket.send_json(chunk_msg.model_dump(mode="json"))
                    
                    # Check if we have complete sentences to send to TTS
                    if request.stream_audio and self.tts_service:
                        while True:
                            # Find the last sentence delimiter
                            last_delimiter_pos = -1
                            for delim in sentence_delimiters:
                                pos = sentence_buffer.rfind(delim)
                                if pos > last_delimiter_pos:
                                    last_delimiter_pos = pos
                            
                            if last_delimiter_pos >= 0:
                                # Extract complete sentence(s)
                                complete_text = sentence_buffer[:last_delimiter_pos + 1].strip()
                                sentence_buffer = sentence_buffer[last_delimiter_pos + 1:]
                                
                                if complete_text:
                                    await sentence_queue.put(complete_text)
                                    logger.debug("Queued for TTS", text=complete_text[:50])
                            else:
                                break
                    
                    await asyncio.sleep(0.001)  # Yield for interruption
                
                # Send any remaining text to TTS
                if request.stream_audio and self.tts_service and sentence_buffer.strip():
                    await sentence_queue.put(sentence_buffer.strip())
                
                # Signal TTS worker to finish
                if tts_task:
                    await sentence_queue.put(None)
                    await tts_task
                
                # Send final text chunk marker
                final_text_msg = ChatStreamResponse(
                    chunk="",
                    chunk_index=self.current_text_chunk_index + 1,
                    is_final=True
                )
                await self.websocket.send_json(final_text_msg.model_dump(mode="json"))
                
                # Send final audio marker if audio was streamed
                if audio_chunks_sent > 0:
                    final_audio_msg = AudioChunk(
                        data="",
                        chunk_index=self.current_audio_chunk_index + 1,
                        is_final=True,
                        size_bytes=0
                    )
                    await self.websocket.send_json(final_audio_msg.model_dump(mode="json"))
                
                logger.info(
                    "Streaming completed",
                    user_id=request.user_id,
                    text_chunks=self.current_text_chunk_index,
                    audio_chunks=audio_chunks_sent,
                    total_text_length=len(full_text)
                )
                
                # Send metadata
                metadata = StreamMetadata(
                    model_used=configuration.model_name,
                    tokens_used=None,
                    execution_time_ms=None,
                    tools_called=[],
                    thread_id=context.get("thread_id"),
                    voice_id=request.voice_id if request.stream_audio else None,
                    total_text_chunks=self.current_text_chunk_index,
                    total_audio_chunks=audio_chunks_sent,
                )
                await self.websocket.send_json(metadata.model_dump(mode="json"))
                
                # Send completion
                complete_msg = CompleteMessage(
                    message="Stream completed successfully",
                    metadata=metadata
                )
                await self.websocket.send_json(complete_msg.model_dump(mode="json"))
                
            finally:
                # Ensure TTS task is cancelled on any error
                if tts_task and not tts_task.done():
                    tts_task.cancel()
                    try:
                        await tts_task
                    except asyncio.CancelledError:
                        pass
            
        except asyncio.CancelledError:
            logger.info(
                "Chat stream task cancelled (interrupted by new message)",
                checkpoint_preserved=True,
                conversation_state="auto-saved by LangGraph"
            )
            raise
            
        except Exception as e:
            logger.error("Chat streaming failed", error=str(e), exc_info=True)
            error_msg = ErrorMessage(
                code="CHAT_STREAMING_ERROR",
                message=f"Chat streaming failed: {str(e)}",
            )
            await self.websocket.send_json(error_msg.model_dump(mode="json"))
            
        finally:
            self.is_streaming = False
    
    async def _cleanup(self):
        """Clean up resources on session end."""
        logger.info("Cleaning up WebSocket session")
        
        # Cancel active task if exists
        if self.active_task and not self.active_task.done():
            self.active_task.cancel()
            try:
                await self.active_task
            except asyncio.CancelledError:
                pass
        
        # Clear message queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
