"""
Thread resolution for LangGraph conversations.

Resolves thread IDs from context for checkpoint management.
"""

from typing import Any, Dict, Optional

from internal.domain.entities import AgentConfiguration


class ThreadResolver:
    """Resolves thread IDs from context."""

    @staticmethod
    def resolve(
        configuration: AgentConfiguration,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """
        Resolve checkpoint thread_id from context.

        Priority: session_id > user_id:agent_id > default

        Args:
            configuration: Agent configuration
            context: Request context with session/user info

        Returns:
            Thread ID string for checkpoint lookup
        """
        if not context:
            return "default"

        session_id = context.get("session_id")
        if session_id:
            return f"session:{session_id}"

        user_id = context.get("user_id")
        if not user_id:
            return "default"

        agent_scope = context.get("agent_id") or configuration.model_name
        return f"user:{user_id}:{agent_scope}"
