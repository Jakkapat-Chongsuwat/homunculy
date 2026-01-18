"""
Pipeline Adapters - OpenAI/LiveKit implementation.

This module provides pipeline adapters for STT/LLM/TTS.
To switch providers, create new adapters implementing the same ports.
"""

from infrastructure.adapters.pipeline.openai_adapter import (
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
