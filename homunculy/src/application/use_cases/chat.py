"""Chat use case - Process text chat input."""

from dataclasses import dataclass
from typing import Any

from common.logger import get_logger
from domain.entities import AgentConfiguration, AgentResponse
from domain.interfaces import LLMPort

logger = get_logger(__name__)


@dataclass
class ChatInput:
    """Chat input DTO."""

    message: str
    config: AgentConfiguration
    thread_id: str
    context: dict[str, Any] | None = None


@dataclass
class ChatOutput:
    """Chat output DTO."""

    response: AgentResponse
    thread_id: str


class ChatUseCase:
    """Process chat input and return response."""

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    async def execute(self, input_: ChatInput) -> ChatOutput:
        """Execute chat processing."""
        logger.info("Processing chat", thread_id=input_.thread_id)
        context = self._build_context(input_)
        response = await self._invoke_llm(input_, context)
        return self._build_output(response, input_.thread_id)

    def _build_context(self, input_: ChatInput) -> dict[str, Any]:
        """Build context for LLM."""
        base = {"thread_id": input_.thread_id}
        return {**base, **(input_.context or {})}

    async def _invoke_llm(
        self,
        input_: ChatInput,
        context: dict[str, Any],
    ) -> AgentResponse:
        """Invoke LLM with message."""
        return await self._llm.chat(input_.config, input_.message, context)

    def _build_output(self, response: AgentResponse, thread_id: str) -> ChatOutput:
        """Build output DTO."""
        return ChatOutput(response=response, thread_id=thread_id)
