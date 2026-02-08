"""
LangGraph Graph Builder - Implements GraphBuilderPort.

This adapter implements the application layer's GraphBuilderPort
using LangGraph's StateGraph. To switch to AutoGen, create a new
adapter implementing the same protocol.
"""

from __future__ import annotations

from typing import Any, Callable, Hashable

from langgraph.graph import END, StateGraph

from common.logger import get_logger
from infrastructure.adapters.llm.state import GraphState
from infrastructure.adapters.tools.rag.graph_builder import GraphBuilderPort

logger = get_logger(__name__)


class LangGraphBuilder(GraphBuilderPort):
    """LangGraph implementation of GraphBuilderPort."""

    def __init__(self, state_class: type = GraphState) -> None:
        self._graph = StateGraph(state_class)
        self._entry_set = False

    def add_node(self, name: str, func: Callable) -> None:
        """Add a node to the graph."""
        self._graph.add_node(name, func)

    def add_edge(self, source: str, target: str) -> None:
        """Add edge between nodes."""
        actual_target = END if target == "__end__" else target
        self._graph.add_edge(source, actual_target)

    def add_conditional_edge(
        self,
        source: str,
        router: Callable,
        routes: dict[str, str],
    ) -> None:
        """Add conditional routing edge."""
        # Convert __end__ to LangGraph END
        resolved: dict[Hashable, str] = {
            k: (END if v == "__end__" else v) for k, v in routes.items()
        }
        self._graph.add_conditional_edges(source, router, resolved)

    def set_entry(self, name: str) -> None:
        """Set entry point."""
        self._graph.set_entry_point(name)
        self._entry_set = True

    def compile(self) -> Any:
        """Compile to executable graph."""
        if not self._entry_set:
            raise ValueError("Entry point not set")
        return self._graph.compile()


def create_langgraph_builder(state_class: type = GraphState) -> LangGraphBuilder:
    """Factory for creating LangGraph builder."""
    return LangGraphBuilder(state_class)
