"""
Streaming Use Cases Package.

This package provides use case implementations for real-time streaming operations
including LLM chat streaming and TTS audio streaming.
"""

from internal.usecases.streaming.interfaces import (
    StreamChatUseCase,
    TTSStreamingUseCase,
)
from internal.usecases.streaming.sentence_buffer import (
    SentenceBuffer,
    create_sentence_buffer,
)
from internal.usecases.streaming.stream_chat_usecase import (
    StreamChatUseCaseImpl,
)
from internal.usecases.streaming.tts_streaming_usecase import (
    TTSStreamingUseCaseImpl,
)

__all__ = [
    # Protocols
    "StreamChatUseCase",
    "TTSStreamingUseCase",
    # Implementations
    "StreamChatUseCaseImpl",
    "TTSStreamingUseCaseImpl",
    # Utilities
    "SentenceBuffer",
    "create_sentence_buffer",
]
