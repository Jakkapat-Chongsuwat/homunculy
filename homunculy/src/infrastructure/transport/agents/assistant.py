"""LiveKit voice assistant agent (infrastructure layer)."""

from dataclasses import dataclass

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool

from common.logger import get_logger
from infrastructure.transport.agents.tools import get_current_time

logger = get_logger(__name__)


@dataclass
class AssistantState:
    """Shared state across agent handoffs."""

    user_name: str | None = None
    current_task: str | None = None
    code_context: str | None = None


INSTRUCTIONS = """You are a friendly AI voice assistant.

PERSONALITY:
- Warm, caring, and genuinely interested in the user
- Speak naturally like a friend, not a formal assistant
- Use the user's name when you know it
- Show empathy and emotional intelligence

VOICE RULES:
- Keep responses SHORT (1-2 sentences for voice)
- No markdown, lists, or formatting - speak naturally
- Match the user's language

CAPABILITIES:
- General conversation and emotional support
- Tell the current time when asked
- Hand off to the coding agent for programming tasks

When the user asks about coding, programming, or technical implementation,
use the handoff_to_coder tool to transfer them to your specialist mode."""


class AssistantAgent(Agent):
    """Main assistant agent - companion mode."""

    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)
        logger.debug("AssistantAgent initialized")

    async def on_enter(self) -> None:
        """Greet user on join."""
        logger.info("on_enter called - generating greeting")
        try:
            await self.session.generate_reply(
                instructions="Greet warmly. If you know their name, use it."
            )
            logger.debug("generate_reply called successfully")
        except Exception as e:
            logger.error("Failed to generate greeting", error=str(e), exc_info=True)

    @function_tool
    async def tell_time(self, context: RunContext[AssistantState]) -> str:
        """Tell the current time when asked."""
        logger.debug("tell_time tool called")
        return f"The current time is {get_current_time()}"

    @function_tool
    async def remember_name(self, context: RunContext[AssistantState], name: str) -> str:
        """Remember the user's name."""
        logger.debug("remember_name tool called", name=name)
        context.userdata.user_name = name
        return f"I'll remember your name, {name}!"

    @function_tool
    async def handoff_to_coder(self, context: RunContext[AssistantState], task: str) -> tuple:
        """Hand off to coding agent for programming tasks."""
        logger.debug("handoff_to_coder tool called", task=task)
        from infrastructure.transport.agents.coder import CoderAgent

        context.userdata.current_task = task
        coder = CoderAgent(context.userdata)
        return coder, f"Switching to coder mode for: {task}"
