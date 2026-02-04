"""Legacy path for LangGraph supervisor adapter."""

from infrastructure.adapters.orchestration.supervisor.adapter import (
    LangGraphSupervisorAdapter,
    SupervisorOrchestrator,
)

__all__ = ["LangGraphSupervisorAdapter", "SupervisorOrchestrator"]
