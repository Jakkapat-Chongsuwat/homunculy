"""Pipecat pipeline definition."""

import os
from typing import Any

from common.logger import get_logger
from livekit.agents import JobContext
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.openai import OpenAISTTService
from pipecat.transports.livekit.transport import LiveKitParams, LiveKitTransport

from internal.adapters.livekit.pipecat.langgraph_llm_service import LangGraphLLMService
from internal.domain.entities import AgentConfiguration, AgentPersonality, AgentProvider
from internal.infrastructure.container import get_llm_service

logger = get_logger(__name__)


async def run_pipeline(ctx: JobContext) -> None:
    transport = _create_transport(ctx)
    task = _create_task(transport, ctx)
    await _run_task(task)


async def _run_task(task: PipelineTask) -> None:
    runner = PipelineRunner()
    await runner.run(task)


def _create_transport(ctx: JobContext) -> LiveKitTransport:
    url, token, room = livekit_parts(ctx)
    return LiveKitTransport(url, token, room, params=_transport_params())


def _transport_params() -> LiveKitParams:
    return LiveKitParams(
        audio_out_enabled=True,
        audio_in_enabled=True,
        camera_in_enabled=False,
        vad_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
        vad_audio_passthrough=True,
    )


def livekit_parts(ctx: Any) -> tuple[str, str, str]:
    return _get_livekit_url(ctx), _get_livekit_token(ctx), _get_livekit_room_name(ctx)


def _get_livekit_url(ctx: Any) -> str:
    return getattr(getattr(ctx, "_info", None), "url", "")


def _get_livekit_token(ctx: Any) -> str:
    return getattr(getattr(ctx, "_info", None), "token", "")


def _get_livekit_room_name(ctx: Any) -> str:
    return getattr(getattr(ctx, "room", None), "name", "")


def _create_task(transport: LiveKitTransport, ctx: JobContext) -> PipelineTask:
    pipeline = Pipeline(processors=_create_processors(transport, ctx))
    return PipelineTask(pipeline, params=_create_params())


def _create_params() -> PipelineParams:
    return PipelineParams(allow_interruptions=True, enable_metrics=True)


def _create_processors(transport: LiveKitTransport, ctx: JobContext) -> list:
    return [
        transport.input(),
        _create_stt(),
        _create_llm_service(ctx),
        _create_tts(),
        transport.output(),
    ]


def _create_stt() -> OpenAISTTService:
    return OpenAISTTService(api_key=_openai_key())


def _create_tts() -> ElevenLabsTTSService:
    return ElevenLabsTTSService(api_key=_elevenlabs_key(), voice_id=_tts_voice_id())


def _openai_key() -> str:
    return os.getenv("OPENAI_API_KEY", "")


def _elevenlabs_key() -> str:
    return os.getenv("ELEVENLABS_API_KEY", "")


def _tts_voice_id() -> str:
    return os.getenv("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")


def _create_llm_service(ctx: JobContext) -> LangGraphLLMService:
    return LangGraphLLMService(get_llm_service(), default_configuration(), _session_id(ctx))


def _session_id(ctx: JobContext) -> str:
    return ctx.room.name


def default_configuration() -> AgentConfiguration:
    return AgentConfiguration(
        provider=AgentProvider.LANGRAPH,
        model_name=default_model(),
        personality=_default_personality(),
        system_prompt=default_system_prompt(),
    )


def _default_personality() -> AgentPersonality:
    return AgentPersonality(name="Default", description="Default assistant")


def default_model() -> str:
    return os.getenv("LLM_DEFAULT_MODEL", "gpt-4o-mini")


def default_system_prompt() -> str:
    return os.getenv("LLM_SYSTEM_PROMPT", "You are a helpful assistant.")
