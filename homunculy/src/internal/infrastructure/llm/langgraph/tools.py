"""
LangGraph Tools for Agent Capabilities.

Tools that can be registered with LangGraph agents to extend their functionality.
Following Clean Architecture, tools depend on domain service interfaces.
"""

from typing import Annotated, Optional
from langchain_core.tools import tool

from common.logger import get_logger
from internal.domain.services import TTSService


logger = get_logger(__name__)


def create_tts_tool(tts_service: TTSService):
    """
    Create a text-to-speech tool for LangGraph agents.
    
    This factory function creates a tool with the TTS service injected,
    allowing the agent to generate speech from text.
    
    Args:
        tts_service: TTS service implementation (injected via DI)
        
    Returns:
        LangChain tool that can be registered with agents
    """
    
    @tool
    async def text_to_speech(
        text: Annotated[str, "The text to convert to speech"],
        voice_id: Annotated[str, "Voice ID to use for synthesis"],
        stability: Annotated[float, "Voice stability (0.0-1.0)"] = 0.5,
        similarity_boost: Annotated[float, "Voice similarity (0.0-1.0)"] = 0.75,
    ) -> str:
        """
        Convert text to speech audio.
        
        Use this tool when you need to generate voice audio from text.
        Returns a status message indicating success or failure.
        """
        try:
            logger.info(
                "Agent invoking TTS tool",
                text_length=len(text),
                voice_id=voice_id
            )
            
            audio_bytes = await tts_service.synthesize(
                text=text,
                voice_id=voice_id,
                stability=stability,
                similarity_boost=similarity_boost,
            )
            
            return f"Successfully generated {len(audio_bytes)} bytes of audio"
            
        except Exception as e:
            logger.error("TTS tool failed", error=str(e), exc_info=True)
            return f"Failed to generate speech: {str(e)}"
    
    return text_to_speech


def create_list_voices_tool(tts_service: TTSService):
    """
    Create a tool to list available TTS voices.
    
    Args:
        tts_service: TTS service implementation (injected via DI)
        
    Returns:
        LangChain tool that can be registered with agents
    """
    
    @tool
    async def list_voices() -> str:
        """
        List available text-to-speech voices.
        
        Use this tool to discover which voices are available for speech synthesis.
        Returns a formatted list of voice names and IDs.
        """
        try:
            logger.info("Agent invoking list voices tool")
            
            voices = await tts_service.get_voices()
            
            if not voices:
                return "No voices available"
            
            voice_list = "\n".join([
                f"- {voice['name']} (ID: {voice['voice_id']})"
                for voice in voices[:10]  # Limit to first 10 voices
            ])
            
            return f"Available voices:\n{voice_list}"
            
        except Exception as e:
            logger.error("List voices tool failed", error=str(e), exc_info=True)
            return f"Failed to list voices: {str(e)}"
    
    return list_voices
