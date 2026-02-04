"""Companion Use Case - Main AI companion entry point.

This is the core use case for the "Yui/Jarvis" style companion.
It orchestrates:
- Persona loading
- Memory retrieval
- Multi-agent routing via supervisor
- Response generation
"""

from dataclasses import dataclass
from typing import Any

from common.logger import get_logger
from domain.interfaces.companion import (
    CompanionOutput,
    EmotionalTone,
)
from domain.interfaces.memory import MemoryPort, MemoryQuery
from domain.interfaces.orchestration import (
    OrchestrationInput,
    OrchestratorPort,
)
from domain.interfaces.persona import PersonaPort

logger = get_logger(__name__)


@dataclass
class CompanionRequest:
    """Request DTO for companion."""

    message: str
    session_id: str
    user_id: str
    channel: str = "default"
    language: str = "en"
    metadata: dict[str, Any] | None = None


@dataclass
class CompanionResponse:
    """Response DTO from companion."""

    message: str
    tone: EmotionalTone
    session_id: str
    metadata: dict[str, Any] | None = None


class CompanionUseCase:
    """Main companion AI use case - like Yui or Jarvis."""

    def __init__(
        self,
        orchestrator: OrchestratorPort,
        memory: MemoryPort,
        persona: PersonaPort,
    ) -> None:
        self._orchestrator = orchestrator
        self._memory = memory
        self._persona = persona

    async def chat(self, request: CompanionRequest) -> CompanionResponse:
        """Main chat entry point."""
        logger.info(
            "Companion chat",
            session_id=request.session_id,
            user_id=request.user_id,
        )
        persona = await self._load_persona(request.user_id)
        memories = await self._retrieve_memories(request)
        context = self._build_context(request, persona, memories)
        output = await self._invoke_orchestrator(request, context)
        await self._save_interaction(request, output)
        return self._build_response(request, output)

    async def _load_persona(self, user_id: str) -> dict[str, Any]:
        """Load persona for user."""
        persona = await self._persona.get_user_persona(user_id)
        return {
            "name": persona.name,
            "system_prompt": persona.system_prompt,
            "speaking_style": persona.speaking_style,
        }

    async def _retrieve_memories(
        self,
        request: CompanionRequest,
    ) -> list[str]:
        """Retrieve relevant memories."""
        query = MemoryQuery(
            query=request.message,
            user_id=request.user_id,
            limit=5,
        )
        result = await self._memory.search(query)
        return [m.content for m in result.memories]

    def _build_context(
        self,
        request: CompanionRequest,
        persona: dict[str, Any],
        memories: list[str],
    ) -> dict[str, Any]:
        """Build context for orchestrator."""
        return {
            "persona": persona,
            "memories": memories,
            "user_id": request.user_id,
            "channel": request.channel,
            "language": request.language,
            **(request.metadata or {}),
        }

    async def _invoke_orchestrator(
        self,
        request: CompanionRequest,
        context: dict[str, Any],
    ) -> CompanionOutput:
        """Invoke orchestrator (supervisor)."""
        input_ = OrchestrationInput(
            message=request.message,
            session_id=request.session_id,
            context=context,
        )
        result = await self._orchestrator.invoke(input_)
        return CompanionOutput(
            message=result.message,
            tone=EmotionalTone.NEUTRAL,
            metadata=result.metadata,
        )

    async def _save_interaction(
        self,
        request: CompanionRequest,
        output: CompanionOutput,
    ) -> None:
        """Save interaction to memory."""
        # TODO: Implement memory storage
        logger.debug(
            "Saving interaction",
            user_id=request.user_id,
            message_length=len(output.message),
        )

    def _build_response(
        self,
        request: CompanionRequest,
        output: CompanionOutput,
    ) -> CompanionResponse:
        """Build response DTO."""
        return CompanionResponse(
            message=output.message,
            tone=output.tone,
            session_id=request.session_id,
            metadata=output.metadata,
        )
