"""RAG Graph Builder - Application layer graph definition.

This module defines WHAT the RAG graph does (nodes, edges, routing).
The actual LangGraph implementation is in infrastructure.

Moved from application/rag_graph/ to be a tool, not the main agent.
"""

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class GraphBuilderPort(Protocol):
    """Protocol for graph builders - framework agnostic."""

    def add_node(self, name: str, func: Callable) -> None:
        """Add a node to the graph."""
        ...

    def add_edge(self, source: str, target: str) -> None:
        """Add edge between nodes."""
        ...

    def add_conditional_edge(
        self,
        source: str,
        router: Callable,
        routes: dict[str, str],
    ) -> None:
        """Add conditional routing edge."""
        ...

    def set_entry(self, name: str) -> None:
        """Set entry point."""
        ...

    def compile(self) -> Any:
        """Compile to executable graph."""
        ...


@dataclass
class RAGGraphConfig:
    """Configuration for RAG graph."""

    retrieve_fn: Callable
    grade_docs_fn: Callable
    generate_fn: Callable
    grade_gen_fn: Callable
    rewrite_fn: Callable
    route_fn: Callable


# Node names (domain constants)
RETRIEVE = "retrieve"
GRADE_DOCS = "grade_documents"
GENERATE = "generate"
GRADE_GEN = "grade_generation"
REWRITE = "rewrite"


def build_rag_graph(config: RAGGraphConfig, builder: GraphBuilderPort) -> Any:
    """Build RAG graph using provided builder.

    This is framework-agnostic - the builder determines
    whether it's LangGraph, AutoGen, or something else.
    """
    _add_nodes(builder, config)
    _add_edges(builder, config.route_fn)
    return builder.compile()


def _add_nodes(builder: GraphBuilderPort, config: RAGGraphConfig) -> None:
    """Add all nodes to graph."""
    builder.add_node(RETRIEVE, config.retrieve_fn)
    builder.add_node(GRADE_DOCS, config.grade_docs_fn)
    builder.add_node(GENERATE, config.generate_fn)
    builder.add_node(GRADE_GEN, config.grade_gen_fn)
    builder.add_node(REWRITE, config.rewrite_fn)


def _add_edges(builder: GraphBuilderPort, route_fn: Callable) -> None:
    """Add edges and routing to graph."""
    builder.set_entry(RETRIEVE)
    builder.add_edge(RETRIEVE, GRADE_DOCS)
    builder.add_conditional_edge(GRADE_DOCS, route_fn, _grade_docs_routes())
    builder.add_edge(GENERATE, GRADE_GEN)
    builder.add_conditional_edge(GRADE_GEN, route_fn, _grade_gen_routes())
    builder.add_edge(REWRITE, RETRIEVE)


def _grade_docs_routes() -> dict[str, str]:
    """Route map for document grading."""
    return {"generate": GENERATE, "rewrite": REWRITE}


def _grade_gen_routes() -> dict[str, str]:
    """Route map for generation grading."""
    return {"end": "__end__", "retry": REWRITE}
