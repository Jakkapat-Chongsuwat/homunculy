"""
Streaming Use Case Protocols.

Defines Protocol-based interfaces for streaming operations using PEP 544.
"""

from typing import Optional, Protocol

from internal.domain.entities import AgentConfiguration


class StreamChatUseCase(Protocol):
    """
    Protocol for streaming chat with LLM and optional TTS.

    Coordinates LLM streaming, text buffering, and TTS audio generation.
    This is the main use case for real-time chat with audio streaming.
    """

    async def execute(
        self,
        message: str,
        configuration: AgentConfiguration,
        context: dict,
        stream_audio: bool,
        voice_id: Optional[str],
        on_text_chunk: Optional[callable],
        on_audio_chunk: Optional[callable],
    ) -> str:
        """
        Execute streaming chat and return full response text.

        Args:
            message: User message to send
            configuration: Agent configuration
            context: Conversation context including user_id
            stream_audio: Whether to generate TTS audio
            voice_id: Voice ID for TTS
            on_text_chunk: Callback for text chunks (chunk, index, is_final)
            on_audio_chunk: Callback for audio chunks (audio_bytes, index, is_final)

        Returns:
            Full response text
        """
        ...


class TTSStreamingUseCase(Protocol):
    """
    Protocol for streaming text-to-speech conversion.

    Converts text sentences to audio chunks in real-time.
    Supports queuing sentences and streaming audio back to caller.
    """

    async def queue_sentence(self, sentence: str) -> None:
        """Queue a sentence for TTS processing."""
        ...

    async def finish(self) -> None:
        """Signal that no more sentences will be queued."""
        ...

    async def run(self) -> None:
        """Run the TTS worker loop."""
        ...

    @property
    def chunks_sent(self) -> int:
        """Get count of audio chunks sent."""
        ...

    @property
    def current_index(self) -> int:
        """Get current chunk index."""
        ...
