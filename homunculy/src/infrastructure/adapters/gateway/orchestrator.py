"""Gateway orchestrator adapter."""

import os
from collections.abc import Callable

from domain.interfaces import (
    DualSystemInput,
    DualSystemPort,
    OrchestrationInput,
    OrchestrationOutput,
    OrchestratorPort,
)


class GatewayOrchestrator(OrchestratorPort):
    """Wrap dual-system for gateway routing."""

    def __init__(self, dual_system_provider: DualSystemPort | Callable[[], DualSystemPort]) -> None:
        self._dual_system_provider = dual_system_provider

    async def invoke(self, input_: OrchestrationInput) -> OrchestrationOutput:
        """Invoke dual-system or fallback."""
        if not _has_llm_key():
            return OrchestrationOutput(message=_fallback(input_))
        output = await self._dual_system().process(_dual_input(input_))
        return OrchestrationOutput(message=output.text)

    def _dual_system(self) -> DualSystemPort:
        """Get dual-system instance lazily."""
        provider = self._dual_system_provider
        return provider() if callable(provider) else provider

    async def stream(self, input_: OrchestrationInput):
        """Stream not supported for gateway (yet)."""
        yield (await self.invoke(input_)).message


def _dual_input(input_: OrchestrationInput) -> DualSystemInput:
    """Map orchestration input to dual-system input."""
    return DualSystemInput(
        text=input_.message, session_id=input_.session_id, context=input_.context
    )


def _has_llm_key() -> bool:
    """Check if LLM key is configured."""
    return bool(os.getenv("LLM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))


def _fallback(input_: OrchestrationInput) -> str:
    """Return fallback response when LLM is not configured."""
    return f"Gateway is not configured yet (session {input_.session_id})."
