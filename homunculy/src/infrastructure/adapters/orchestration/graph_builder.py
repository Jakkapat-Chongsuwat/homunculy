"""Legacy path for LangGraph graph builder adapter."""

from infrastructure.adapters.orchestration.langgraph.graph_builder import (
    LangGraphBuilder,
    create_langgraph_builder,
)

__all__ = ["LangGraphBuilder", "create_langgraph_builder"]
