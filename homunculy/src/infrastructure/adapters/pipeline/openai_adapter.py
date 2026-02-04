"""Legacy path for OpenAI pipeline adapter."""

from infrastructure.adapters.pipeline.openai.adapter import (
    OpenAIPipeline,
    OpenAISTT,
    OpenAITTS,
    SileroVAD,
    create_openai_pipeline,
)

__all__ = [
    "OpenAIPipeline",
    "OpenAISTT",
    "OpenAITTS",
    "SileroVAD",
    "create_openai_pipeline",
]
