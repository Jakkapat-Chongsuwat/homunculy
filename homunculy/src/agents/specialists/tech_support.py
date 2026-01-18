"""
Tech Support Specialist Agent.

Handles technical support conversations:
- Troubleshooting
- Bug reports
- Feature questions
- Documentation guidance

This is a PLACEHOLDER for future implementation.
"""

from __future__ import annotations

from livekit.agents import Agent


class TechSupportAgent(Agent):
    """Technical support specialist sub-agent."""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a technical support specialist.

Help users with:
- Troubleshooting issues
- Understanding error messages
- Finding documentation
- Explaining technical concepts

Be patient, thorough, and guide step-by-step."""
        )

    async def on_enter(self) -> None:
        """Called when agent takes over."""
        self.session.generate_reply(
            instructions="Introduce yourself as the tech support specialist."
        )
