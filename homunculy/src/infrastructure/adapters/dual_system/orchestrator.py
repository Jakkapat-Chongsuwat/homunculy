"""
Dual-System Orchestrator - Coordinates reflex + cognition.

This is the main entry point for human-like interaction.
It runs reflex and cognition in parallel:
- Reflex provides immediate acknowledgment
- Cognition processes deep reasoning
- User hears reflex while waiting for cognition
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from domain.interfaces.dual_system import (
    CognitionPort,
    DualSystemInput,
    DualSystemOutput,
    DualSystemPort,
    EmotionDetectorPort,
    ReflexPort,
    ResponseType,
)

if TYPE_CHECKING:
    pass


class DualSystemOrchestrator(DualSystemPort):
    """Orchestrates reflex + cognition for human-like interaction."""

    def __init__(
        self,
        reflex: ReflexPort,
        cognition: CognitionPort,
        emotion_detector: EmotionDetectorPort,
    ) -> None:
        """Initialize with reflex and cognition adapters."""
        self._reflex = reflex
        self._cognition = cognition
        self._emotion = emotion_detector
        self._active_sessions: dict[str, asyncio.Task] = {}

    async def process(self, input_: DualSystemInput) -> DualSystemOutput:
        """Process with dual-system architecture."""
        # 1. Detect emotion
        emotion = await self._emotion.detect(input_)

        # 2. Check if reflex can fully handle
        if self._reflex.can_handle(input_):
            reflex_out = await self._reflex.respond(input_)
            return DualSystemOutput(
                response_type=ResponseType.REFLEX,
                text=reflex_out.text,
                reflex=reflex_out,
                emotion=emotion,
            )

        # 3. For complex input: run cognition
        cognition_out = await self._cognition.reason(input_)
        return DualSystemOutput(
            response_type=ResponseType.COGNITION,
            text=cognition_out.text,
            cognition=cognition_out,
            emotion=emotion,
        )

    async def stream(self, input_: DualSystemInput) -> AsyncIterator[DualSystemOutput]:
        """Stream responses - reflex first, then cognition."""
        emotion = await self._emotion.detect(input_)

        # 1. If reflex can handle, just yield that
        if self._reflex.can_handle(input_):
            reflex_out = await self._reflex.respond(input_)
            yield DualSystemOutput(
                response_type=ResponseType.REFLEX,
                text=reflex_out.text,
                reflex=reflex_out,
                emotion=emotion,
            )
            return

        # 2. Yield reflex filler immediately
        reflex_out = await self._reflex.respond(input_)
        if reflex_out.is_filler:
            yield DualSystemOutput(
                response_type=ResponseType.REFLEX,
                text=reflex_out.text,
                reflex=reflex_out,
                emotion=emotion,
            )

        # 3. Stream cognition
        async for chunk in self._cognition.stream(input_):
            yield DualSystemOutput(
                response_type=ResponseType.COGNITION,
                text=chunk,
                emotion=emotion,
            )

    async def interrupt(self, session_id: str) -> None:
        """Interrupt ongoing cognition."""
        if session_id in self._active_sessions:
            self._active_sessions[session_id].cancel()
            del self._active_sessions[session_id]


def create_dual_system(
    reflex: ReflexPort,
    cognition: CognitionPort,
    emotion: EmotionDetectorPort,
) -> DualSystemPort:
    """Factory for creating dual-system orchestrator."""
    return DualSystemOrchestrator(reflex, cognition, emotion)
