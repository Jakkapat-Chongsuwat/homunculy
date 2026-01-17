"""Pipecat pipeline - STT -> LangGraph -> TTS flow."""

import os
from dataclasses import dataclass
from typing import Any

from common.logger import get_logger
from livekit.agents import JobContext
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.services.openai import OpenAISTTService

from infrastructure.pipecat.transport import (
    TransportConfig,
    create_livekit_transport,
    extract_livekit_parts,
)

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Pipeline configuration."""

    openai_key: str
    elevenlabs_key: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    allow_interruptions: bool = True
    enable_metrics: bool = True


class PipecatPipeline:
    """Pipecat audio pipeline wrapper."""

    def __init__(self, config: PipelineConfig, llm_service: Any) -> None:
        self._config = config
        self._llm_service = llm_service

    async def run(self, ctx: JobContext) -> None:
        """Run the pipeline for a LiveKit context."""
        transport = self._create_transport(ctx)
        task = self._create_task(transport)
        await self._execute(task)

    def _create_transport(self, ctx: JobContext) -> Any:
        """Create LiveKit transport."""
        url, token, room = extract_livekit_parts(ctx)
        return create_livekit_transport(url, token, room, TransportConfig())

    def _create_task(self, transport: Any) -> PipelineTask:
        """Create pipeline task."""
        processors = self._build_processors(transport)
        pipeline = Pipeline(processors=processors)
        return PipelineTask(pipeline, params=self._task_params())

    def _build_processors(self, transport: Any) -> list:
        """Build processor chain."""
        return [
            transport.input(),
            self._create_stt(),
            self._llm_service,
            self._create_tts(),
            transport.output(),
        ]

    def _create_stt(self) -> OpenAISTTService:
        """Create STT service."""
        return OpenAISTTService(api_key=self._config.openai_key)

    def _create_tts(self) -> ElevenLabsTTSService:
        """Create TTS service."""
        return ElevenLabsTTSService(
            api_key=self._config.elevenlabs_key,
            voice_id=self._config.voice_id,
        )

    def _task_params(self) -> PipelineParams:
        """Build task parameters."""
        return PipelineParams(
            allow_interruptions=self._config.allow_interruptions,
            enable_metrics=self._config.enable_metrics,
        )

    async def _execute(self, task: PipelineTask) -> None:
        """Execute pipeline task."""
        runner = PipelineRunner()
        await runner.run(task)


def create_pipeline(llm_service: Any, config: PipelineConfig | None = None) -> PipecatPipeline:
    """Factory to create pipeline with defaults."""
    cfg = config or _default_config()
    return PipecatPipeline(cfg, llm_service)


def _default_config() -> PipelineConfig:
    """Create default config from environment."""
    return PipelineConfig(
        openai_key=os.getenv("OPENAI_API_KEY", ""),
        elevenlabs_key=os.getenv("ELEVENLABS_API_KEY", ""),
        voice_id=os.getenv("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
    )
