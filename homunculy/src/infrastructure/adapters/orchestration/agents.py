"""Legacy path for supervisor agent factories."""

from infrastructure.adapters.orchestration.supervisor.agents import (
    create_companion_agent,
    create_math_agent,
    create_researcher_agent,
    register_all_agents,
)

__all__ = [
    "create_companion_agent",
    "create_math_agent",
    "create_researcher_agent",
    "register_all_agents",
]
