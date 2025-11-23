"""TTS-specific exceptions."""


class TTSServiceError(Exception):
    """Base exception for TTS service errors."""
    pass


class TTSVoiceNotFoundError(TTSServiceError):
    """Raised when requested voice is not available."""
    pass


class TTSSynthesisError(TTSServiceError):
    """Raised when speech synthesis fails."""
    pass
