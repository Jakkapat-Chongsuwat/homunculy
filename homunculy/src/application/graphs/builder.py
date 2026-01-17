"""Graph builder - Compile LangGraph state machine."""

from typing import Any

from langgraph.graph import END, StateGraph

from application.graphs.state import GraphState

# Node names
RETRIEVE = "retrieve"
GRADE_DOCS = "grade_documents"
GENERATE = "generate"
GRADE_GEN = "grade_generation"
REWRITE = "rewrite"


def build_rag_graph(
    retrieve_fn,
    grade_docs_fn,
    generate_fn,
    grade_gen_fn,
    rewrite_fn,
    route_fn,
) -> Any:
    """Build and compile RAG workflow graph."""
    graph = _create_graph()
    _add_nodes(graph, retrieve_fn, grade_docs_fn, generate_fn, grade_gen_fn, rewrite_fn)
    _add_edges(graph, route_fn)
    return graph.compile()


def _create_graph() -> StateGraph:
    """Create empty state graph."""
    return StateGraph(GraphState)


def _add_nodes(
    graph: StateGraph,
    retrieve_fn,
    grade_docs_fn,
    generate_fn,
    grade_gen_fn,
    rewrite_fn,
) -> None:
    """Add all nodes to graph."""
    graph.add_node(RETRIEVE, retrieve_fn)
    graph.add_node(GRADE_DOCS, grade_docs_fn)
    graph.add_node(GENERATE, generate_fn)
    graph.add_node(GRADE_GEN, grade_gen_fn)
    graph.add_node(REWRITE, rewrite_fn)


def _add_edges(graph: StateGraph, route_fn) -> None:
    """Add edges and routing to graph."""
    graph.set_entry_point(RETRIEVE)
    graph.add_edge(RETRIEVE, GRADE_DOCS)
    graph.add_conditional_edges(GRADE_DOCS, route_fn, _grade_docs_routes())  # type: ignore[arg-type]
    graph.add_edge(GENERATE, GRADE_GEN)
    graph.add_conditional_edges(GRADE_GEN, route_fn, _grade_gen_routes())  # type: ignore[arg-type]
    graph.add_edge(REWRITE, RETRIEVE)


def _grade_docs_routes() -> dict[str, str]:
    """Route map for document grading."""
    return {"generate": GENERATE, "rewrite": REWRITE}


def _grade_gen_routes() -> dict[str, str]:
    """Route map for generation grading."""
    return {"useful": END, "not_useful": REWRITE}
