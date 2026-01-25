"""LiveKit coding agent (infrastructure layer)."""

from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool

from infrastructure.transport.agents.assistant import AssistantState
from infrastructure.transport.agents.tools import execute_code

INSTRUCTIONS = """You are the assistant in Coder Mode - a skilled programmer.

PERSONALITY:
- Warm and friendly, but focused
- Explain code simply, like teaching a friend
- Celebrate successes with the user

VOICE RULES:
- Keep explanations SHORT for voice
- For complex code, summarize the approach first
- Offer to explain more if they want details

CAPABILITIES:
- Write and explain code
- Debug issues
- Suggest best practices
- Execute code in sandbox (when available)

When the coding task is complete, use handoff_to_companion
to return to normal conversation mode."""


class CoderAgent(Agent):
    """Coder mode - handles programming tasks."""

    def __init__(self, state: AssistantState) -> None:
        task_context = f"\nCurrent task: {state.current_task}" if state.current_task else ""
        name_context = f"\nUser's name: {state.user_name}" if state.user_name else ""

        super().__init__(instructions=INSTRUCTIONS + task_context + name_context)
        self._state = state

    async def on_enter(self) -> None:
        """Acknowledge the coding task."""
        self.session.generate_reply(instructions="Briefly acknowledge the task and start helping.")

    @function_tool
    async def run_code(
        self, context: RunContext[AssistantState], code: str, language: str = "python"
    ) -> str:
        """Execute code in a sandbox."""
        return await execute_code(code, language)

    @function_tool
    async def handoff_to_companion(self, context: RunContext[AssistantState]) -> tuple:
        """Return to companion mode after coding is done."""
        from infrastructure.transport.agents.assistant import AssistantAgent

        context.userdata.current_task = None
        companion = AssistantAgent()
        return companion, "Back to companion mode!"
