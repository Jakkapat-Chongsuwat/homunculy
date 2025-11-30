"""
ElevenLabs TTS Service Implementation.

Concrete implementation of TTSService using ElevenLabs API.
"""

from typing import AsyncIterator, Optional
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings

from common.logger import get_logger
from settings.tts import tts_settings
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
        model_id: Optional[str] = None,
        stability: Optional[float] = None,
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None,
    ) -> bytes:
        """
        Synthesize text to speech using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model_id: TTS model to use (defaults to settings)
            stability: Voice stability (0.0-1.0, defaults to settings)
            similarity_boost: Voice similarity (0.0-1.0, defaults to settings)
            style: Voice style exaggeration (0.0-1.0, defaults to settings)
            use_speaker_boost: Enable speaker boost (defaults to settings)
            
        Returns:
            Audio data as bytes (MP3 format)
            
        Raises:
            TTSSynthesisError: If synthesis fails
        """
        # Apply defaults from settings
        model_id = model_id or tts_settings.elevenlabs_model_id
        stability = stability if stability is not None else tts_settings.default_stability
        similarity_boost = similarity_boost if similarity_boost is not None else tts_settings.default_similarity_boost
        style = style if style is not None else tts_settings.default_style
        use_speaker_boost = use_speaker_boost if use_speaker_boost is not None else tts_settings.default_use_speaker_boost
        
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
        Stream text to speech audio chunks using ElevenLabs.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model_id: TTS model to use (defaults to settings)
            stability: Voice stability (0.0-1.0, defaults to settings)
            similarity_boost: Voice similarity (0.0-1.0, defaults to settings)
            style: Voice style exaggeration (0.0-1.0, defaults to settings)
            use_speaker_boost: Enable speaker boost (defaults to settings)
            
        Yields:
            Audio chunks as bytes (MP3 format)
            
        Raises:
            TTSSynthesisError: If streaming fails
        """
        # Apply defaults from settings
        model_id = model_id or tts_settings.elevenlabs_streaming_model_id
        stability = stability if stability is not None else tts_settings.default_stability
        similarity_boost = similarity_boost if similarity_boost is not None else tts_settings.default_similarity_boost
        style = style if style is not None else tts_settings.default_style
        use_speaker_boost = use_speaker_boost if use_speaker_boost is not None else tts_settings.default_use_speaker_boost
        
        logger.info(
            "Starting TTS streaming",
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
        
        # Return the async iterator directly from ElevenLabs
        return self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
            output_format=tts_settings.elevenlabs_output_format,
        )
    
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
