"""
Supervisor Agent - Orchestrates Sub-agents.

The Supervisor is the "brain" that:
1. Receives user input from LiveKit
2. Decides which specialist sub-agent should handle
3. Delegates to the appropriate sub-agent
4. Returns the response

Uses LangGraph for state management and handoffs.
"""

from agents.supervisor.agent import SessionContext, SupervisorAgent, create_supervisor

__all__ = ["SessionContext", "SupervisorAgent", "create_supervisor"]
