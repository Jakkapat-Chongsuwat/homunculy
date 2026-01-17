"""Voice use case - Process voice input via STT -> LLM -> TTS."""

from dataclasses import dataclass
from typing import Any

from common.logger import get_logger
from domain.entities import AgentConfiguration, AgentResponse
from domain.interfaces import LLMPort, STTPort, TTSPort

logger = get_logger(__name__)


@dataclass
class VoiceInput:
    """Voice input DTO."""

    audio: bytes
    config: AgentConfiguration
    thread_id: str
    voice_id: str
    context: dict[str, Any] | None = None


@dataclass
class VoiceOutput:
    """Voice output DTO."""

    audio: bytes
    transcript: str
    response_text: str
    thread_id: str


class VoiceUseCase:
    """Process voice input: STT -> LLM -> TTS."""

    def __init__(self, stt: STTPort, llm: LLMPort, tts: TTSPort) -> None:
        self._stt = stt
        self._llm = llm
        self._tts = tts

    async def execute(self, input_: VoiceInput) -> VoiceOutput:
        """Execute voice processing pipeline."""
        logger.info("Processing voice", thread_id=input_.thread_id)
        transcript = await self._transcribe(input_.audio)
        response = await self._generate(transcript, input_)
        audio = await self._synthesize(response.message, input_.voice_id)
        return self._build_output(transcript, response, audio, input_.thread_id)

    async def _transcribe(self, audio: bytes) -> str:
        """Transcribe audio to text."""
        return await self._stt.transcribe(audio)

    async def _generate(
        self,
        transcript: str,
        input_: VoiceInput,
    ) -> AgentResponse:
        """Generate LLM response."""
        context = {"thread_id": input_.thread_id, **(input_.context or {})}
        return await self._llm.chat(input_.config, transcript, context)

    async def _synthesize(self, text: str, voice_id: str) -> bytes:
        """Synthesize text to speech."""
        return await self._tts.synthesize(text, voice_id)

    def _build_output(
        self,
        transcript: str,
        response: AgentResponse,
        audio: bytes,
        thread_id: str,
    ) -> VoiceOutput:
        """Build output DTO."""
        return VoiceOutput(
            audio=audio,
            transcript=transcript,
            response_text=response.message,
            thread_id=thread_id,
        )
