"""
Sales Specialist Agent.

Handles sales-related conversations:
- Product inquiries
- Pricing questions
- Demo scheduling
- Lead qualification

This is a PLACEHOLDER for future implementation.
"""

from __future__ import annotations

from livekit.agents import Agent


class SalesAgent(Agent):
    """Sales specialist sub-agent."""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a sales specialist.

Help users with:
- Product information
- Pricing questions
- Scheduling demos
- Understanding features

Be professional, helpful, and guide toward next steps."""
        )

    async def on_enter(self) -> None:
        """Called when agent takes over."""
        self.session.generate_reply(instructions="Introduce yourself as the sales specialist.")
