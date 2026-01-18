"""
Agents Package - Agent definitions.

This package contains agent implementations:
- companion/ - Primary conversational agent (human-like friend)
- supervisor/ - Orchestrates sub-agents via LangGraph
- specialists/ - Specialized sub-agents (sales, support, etc.)
- session.py - Session lifecycle management

The Control Plane (Go Management Service) dispatches rooms.
The Companion handles general chat. Supervisor routes to specialists.
"""

from agents.companion import CompanionAgent, CompanionContext, create_companion
from agents.session import AgentSession, SessionState, SessionStatus, create_session_id
from agents.supervisor import SessionContext, SupervisorAgent, create_supervisor

__all__ = [
    "AgentSession",
    "CompanionAgent",
    "CompanionContext",
    "SessionContext",
    "SessionState",
    "SessionStatus",
    "SupervisorAgent",
    "create_companion",
    "create_session_id",
    "create_supervisor",
]
