"""
Orchestration Adapters - LangGraph implementation.

This module provides the LangGraph adapter for OrchestrationPort.
To switch to AutoGen, create autogen_adapter.py implementing the same ports.
"""

from infrastructure.adapters.orchestration.agents import (
    create_companion_agent,
    create_math_agent,
    create_researcher_agent,
    register_all_agents,
)
from infrastructure.adapters.orchestration.graph_builder import (
    LangGraphBuilder,
    create_langgraph_builder,
)
from infrastructure.adapters.orchestration.langgraph_adapter import (
    LangGraphOrchestrator,
    LangGraphSupervisor,
)
from infrastructure.adapters.orchestration.supervisor_adapter import (
    LangGraphSupervisorAdapter,
    SupervisorOrchestrator,
)

__all__ = [
    # Core adapters
    "LangGraphOrchestrator",
    "LangGraphSupervisor",
    # Official supervisor (langgraph-supervisor-py)
    "LangGraphSupervisorAdapter",
    "SupervisorOrchestrator",
    # Graph builder
    "LangGraphBuilder",
    "create_langgraph_builder",
    # Agent factories
    "create_companion_agent",
    "create_math_agent",
    "create_researcher_agent",
    "register_all_agents",
]
