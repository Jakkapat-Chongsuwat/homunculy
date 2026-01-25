"""LiveKit Agent Worker - Voice Assistant.

Architecture:
1. Agent joins LiveKit room as a participant
2. Uses handoff pattern for mode switching (companion ↔ coder)
3. All config from environment (12-factor app)

Flow:
    User speaks → STT → Assistant → handoff if needed → TTS → User hears
"""

from __future__ import annotations

import os
import sys

from livekit.agents import (
    AgentSession,
    ConversationItemAddedEvent,
    JobContext,
    UserInputTranscribedEvent,
    WorkerOptions,
    cli,
)
from livekit.plugins import elevenlabs, openai, silero

from common.logger import configure_logging, get_logger
from infrastructure.transport.agents import AssistantAgent, AssistantState

configure_logging()
logger = get_logger(__name__)


AGENT_NAME = os.getenv("AGENT_NAME", "assistant")
VOICE_ID = os.getenv("TTS_DEFAULT_VOICE_ID", "lhTvHflPVOqgSWyuWQry")
TTS_MODEL = os.getenv("TTS_ELEVENLABS_STREAMING_MODEL_ID", "eleven_turbo_v2_5")
LLM_MODEL = os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")


async def entrypoint(ctx: JobContext) -> None:
    """Agent entrypoint - assistant joins the room."""
    room = ctx.room.name if ctx.room else "unknown"
    logger.info("Assistant joining room", room=room)

    await ctx.connect()
    participant = await ctx.wait_for_participant()
    logger.info("User joined", identity=participant.identity)

    session = _create_session()

    _register_debug_handlers(session)

    await session.start(agent=AssistantAgent(), room=ctx.room)
    logger.info("Assistant session started", room=room)


def _register_debug_handlers(session: AgentSession) -> None:
    """Register event handlers for debugging."""

    @session.on("user_input_transcribed")
    def on_transcribed(event: UserInputTranscribedEvent):
        logger.info(
            "User speech transcribed",
            transcript=event.transcript,
            is_final=event.is_final,
            language=getattr(event, "language", "unknown"),
        )

    @session.on("conversation_item_added")
    def on_item_added(event: ConversationItemAddedEvent):
        item = event.item
        role = getattr(item, "role", "unknown")
        text_content = getattr(item, "text_content", None)
        interrupted = getattr(item, "interrupted", False)
        logger.info(
            "Conversation item added",
            role=role,
            text=text_content[:100] if text_content else None,
            interrupted=interrupted,
        )

    @session.on("agent_state_changed")
    def on_state_changed(event):
        logger.info("Agent state changed", state=str(event))

    logger.debug("Debug event handlers registered")


def _create_session() -> AgentSession[AssistantState]:
    """Create agent session with assistant state."""
    return AgentSession[AssistantState](
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(model=LLM_MODEL),
        tts=elevenlabs.TTS(voice_id=VOICE_ID, model=TTS_MODEL),
        userdata=AssistantState(),
    )


def run_worker() -> None:
    """Run LiveKit agent worker."""
    logger.info("Starting assistant worker", agent_name=AGENT_NAME)
    if len(sys.argv) == 1:
        sys.argv.append("start")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=AGENT_NAME))


if __name__ == "__main__":
    run_worker()
