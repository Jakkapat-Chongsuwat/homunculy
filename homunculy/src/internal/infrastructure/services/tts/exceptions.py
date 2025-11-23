"""TTS-specific exceptions."""


class TTSServiceError(Exception):
    """Base exception for TTS service errors."""
    
    def __init__(self, message: str, **kwargs):
        self.message = message
        self.context = kwargs
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class TTSVoiceNotFoundError(TTSServiceError):
    """Raised when requested voice is not available."""
    
    def __init__(self, voice_id: str, available_voices: list[str] | None = None):
        super().__init__(
            f"Voice not found: {voice_id}",
            voice_id=voice_id,
            available_voices=available_voices
        )


class TTSSynthesisError(TTSServiceError):
    """Raised when speech synthesis fails."""
    
    def __init__(self, message: str, text_length: int | None = None):
        super().__init__(
            f"Speech synthesis failed: {message}",
            text_length=text_length
        )


class TTSAuthenticationError(TTSServiceError):
    """Raised when TTS API authentication fails."""
    
    def __init__(self, provider: str = "elevenlabs"):
        super().__init__(
            f"TTS authentication failed",
            provider=provider
        )


class TTSQuotaExceededError(TTSServiceError):
    """Raised when TTS API quota is exceeded."""
    
    def __init__(self, provider: str = "elevenlabs"):
        super().__init__(
            f"TTS quota exceeded",
            provider=provider
        )


__all__ = [
    "TTSServiceError",
    "TTSVoiceNotFoundError",
    "TTSSynthesisError",
    "TTSAuthenticationError",
    "TTSQuotaExceededError",
]

