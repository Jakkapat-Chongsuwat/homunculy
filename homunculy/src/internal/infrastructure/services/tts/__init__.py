"""
Text-to-Speech Service Implementation.

Implements TTSService using external TTS providers.
"""

from .elevenlabs_provider import ElevenLabsTTSService
from .exceptions import (
    TTSServiceError,
    TTSSynthesisError,
    TTSVoiceNotFoundError,
)

__all__ = [
    "ElevenLabsTTSService",
    "TTSServiceError",
    "TTSSynthesisError",
    "TTSVoiceNotFoundError",
]
