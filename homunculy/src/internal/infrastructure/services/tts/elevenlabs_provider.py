"""
ElevenLabs TTS Service Implementation.

Concrete implementation of TTSService using ElevenLabs API.
"""

from typing import Optional
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings

from common.logger import get_logger
from internal.domain.services.tts_service import TTSService
from .exceptions import TTSServiceError, TTSSynthesisError, TTSVoiceNotFoundError


logger = get_logger(__name__)


class ElevenLabsTTSService(TTSService):
    """ElevenLabs implementation of TTS service."""
    
    def __init__(self, api_key: str):
        """
        Initialize ElevenLabs TTS service.
        
        Args:
            api_key: ElevenLabs API key
        """
        self.client = AsyncElevenLabs(api_key=api_key)
        logger.info("ElevenLabs TTS service initialized")
    
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
        Synthesize text to speech using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model_id: TTS model to use
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity (0.0-1.0)
            style: Voice style exaggeration (0.0-1.0)
            use_speaker_boost: Enable speaker boost
            
        Returns:
            Audio data as bytes (MP3 format)
            
        Raises:
            TTSSynthesisError: If synthesis fails
        """
        try:
            logger.info(
                "Synthesizing speech",
                voice_id=voice_id,
                model=model_id,
                text_length=len(text)
            )
            
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost,
                style=style,
                use_speaker_boost=use_speaker_boost,
            )
            
            # Generate audio (returns AsyncIterator, not awaitable)
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
            )
            
            # Collect audio bytes
            audio_bytes = b""
            async for chunk in audio_generator:
                audio_bytes += chunk
            
            logger.info(
                "Speech synthesis completed",
                audio_size=len(audio_bytes),
                voice_id=voice_id
            )
            
            return audio_bytes
            
        except Exception as e:
            logger.error(
                "Speech synthesis failed",
                error=str(e),
                voice_id=voice_id,
                exc_info=True
            )
            raise TTSSynthesisError(f"Failed to synthesize speech: {str(e)}") from e
    
    async def get_voices(self) -> list[dict]:
        """
        Get available voices from ElevenLabs.
        
        Returns:
            List of voice metadata dictionaries
            
        Raises:
            TTSServiceError: If fetching voices fails
        """
        try:
            logger.debug("Fetching available voices from ElevenLabs")
            
            response = await self.client.voices.get_all()
            
            voices = [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "labels": voice.labels,
                }
                for voice in response.voices
            ]
            
            logger.info("Voices fetched", count=len(voices))
            return voices
            
        except Exception as e:
            logger.error("Failed to fetch voices", error=str(e), exc_info=True)
            raise TTSServiceError(f"Failed to fetch voices: {str(e)}") from e
