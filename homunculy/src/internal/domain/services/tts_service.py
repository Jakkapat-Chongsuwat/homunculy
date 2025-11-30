"""
Text-to-Speech Service Interface.

Domain-level abstraction for TTS interactions.
This belongs in the domain layer as it defines a contract that
infrastructure implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from settings.tts import tts_settings


class TTSService(ABC):
    """
    Abstract interface for Text-to-Speech service interactions.
    
    This interface allows the use case layer and tools to depend on an abstraction
    rather than concrete implementations, following the Dependency Inversion Principle.
    """
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None,
    ) -> bytes:
        """
        Synthesize text to speech audio.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID from TTS provider
            model_id: TTS model to use (defaults to settings)
            stability: Voice stability (0.0-1.0, defaults to settings)
            similarity_boost: Voice similarity (0.0-1.0, defaults to settings)
            style: Voice style exaggeration (0.0-1.0, defaults to settings)
            use_speaker_boost: Enable speaker boost (defaults to settings)
            
        Returns:
            Audio data as bytes (MP3 format)
            
        Raises:
            TTSServiceError: If synthesis fails
        """
        pass
    
    @abstractmethod
    def stream(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None,
    ) -> AsyncIterator[bytes]:
        """
        Stream text to speech audio chunks.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID from TTS provider
            model_id: TTS model to use (defaults to settings)
            stability: Voice stability (0.0-1.0, defaults to settings)
            similarity_boost: Voice similarity (0.0-1.0, defaults to settings)
            style: Voice style exaggeration (0.0-1.0, defaults to settings)
            use_speaker_boost: Enable speaker boost (defaults to settings)
            
        Yields:
            Audio chunks as bytes (format depends on settings)
            
        Raises:
            TTSServiceError: If streaming fails
        """
        pass
    
    @abstractmethod
    async def get_voices(self) -> list[dict]:
        """
        Get available voices from TTS provider.
        
        Returns:
            List of voice metadata dictionaries
            
        Raises:
            TTSServiceError: If fetching voices fails
        """
        pass
