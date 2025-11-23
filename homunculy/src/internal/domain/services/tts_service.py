"""
Text-to-Speech Service Interface.

Domain-level abstraction for TTS interactions.
This belongs in the domain layer as it defines a contract that
infrastructure implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Optional


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
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
    ) -> bytes:
        """
        Synthesize text to speech audio.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID from TTS provider
            model_id: TTS model to use
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity (0.0-1.0)
            style: Voice style exaggeration (0.0-1.0)
            use_speaker_boost: Enable speaker boost
            
        Returns:
            Audio data as bytes (MP3 format)
            
        Raises:
            TTSServiceError: If synthesis fails
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
