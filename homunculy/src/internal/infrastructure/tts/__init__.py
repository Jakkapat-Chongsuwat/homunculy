"""Text-to-Speech Infrastructure."""

from .elevenlabs_service import ElevenLabsTTSService
from .exceptions import TTSServiceError

__all__ = ["ElevenLabsTTSService", "TTSServiceError"]
