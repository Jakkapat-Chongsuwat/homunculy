"""
Cognition Adapter - Deep reasoning layer.

Uses LangGraph for complex reasoning:
- Multi-step tool use
- Research and synthesis
- Code generation
- Stateful conversation with checkpointing
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from domain.interfaces.dual_system import (
    CognitionOutput,
    CognitionPort,
    DualSystemInput,
)

if TYPE_CHECKING:
    from domain.interfaces import CheckpointerPort, OrchestratorPort


class CognitionAdapter(CognitionPort):
    """Deep reasoning using LangGraph orchestrator."""

    def __init__(
        self,
        orchestrator: "OrchestratorPort",
        checkpointer: "CheckpointerPort | None" = None,
    ) -> None:
        """Initialize with orchestrator and optional checkpointer."""
        self._orchestrator = orchestrator
        self._checkpointer = checkpointer

    async def reason(self, input_: DualSystemInput) -> CognitionOutput:
        """Deep reasoning with full context."""
        from domain.interfaces import OrchestrationInput

        orch_input = OrchestrationInput(
            message=input_.text,
            session_id=input_.session_id,
            context=dict(input_.context),
        )
        result = await self._orchestrator.invoke(orch_input)
        return CognitionOutput(
            text=result.message,
            tool_calls=result.tool_calls,
            metadata=result.metadata,
        )

    async def stream(self, input_: DualSystemInput) -> AsyncIterator[str]:
        """Stream reasoning output."""
        from domain.interfaces import OrchestrationInput

        orch_input = OrchestrationInput(
            message=input_.text,
            session_id=input_.session_id,
            context=dict(input_.context),
        )
        async for chunk in self._orchestrator.stream(orch_input):
            yield chunk
