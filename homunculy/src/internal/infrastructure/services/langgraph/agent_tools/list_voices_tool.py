"""
List Voices Tool for LangGraph Agents.

Allows agents to discover available TTS voices.
"""

from common.logger import get_logger
from langchain_core.tools import tool

from internal.domain.services import TTSService

logger = get_logger(__name__)


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

            voice_list = "\n".join(
                [
                    f"- {voice['name']} (ID: {voice['voice_id']})"
                    for voice in voices[:10]  # Limit to first 10 voices
                ]
            )

            return f"Available voices:\n{voice_list}"

        except Exception as e:
            logger.error("List voices tool failed", error=str(e), exc_info=True)
            return f"Failed to list voices: {str(e)}"

    return list_voices
