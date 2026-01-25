"""Graph workflow definitions.

Note: LangGraph-specific GraphState with reducers is in
infrastructure.adapters.langgraph.state.

This module exports framework-agnostic GraphStateBase for
application layer type hints.
"""

from application.graphs.builder import build_rag_graph
from application.graphs.state import GraphStateBase

__all__ = [
    "GraphStateBase",
    "build_rag_graph",
]
