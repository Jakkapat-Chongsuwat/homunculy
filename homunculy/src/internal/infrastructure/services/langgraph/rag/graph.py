"""Self-Reflective RAG Graph."""

from typing import Any, Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import RAGNodes
from .state import RAGState


class SelfReflectiveRAGGraph:
    """Builds self-reflective RAG workflow graph."""

    def __init__(self, nodes: RAGNodes) -> None:
        """Initialize graph builder with injected nodes."""
        self._nodes = nodes
        self.graph: CompiledStateGraph[RAGState, Any, RAGState, RAGState] | None = None

    def build(self) -> CompiledStateGraph[RAGState, Any, RAGState, RAGState]:
        """Build and compile the self-reflective RAG graph."""
        workflow: StateGraph[RAGState] = StateGraph(RAGState)
        self.add_nodes(workflow)
        self.add_edges(workflow)
        self.graph = workflow.compile()
        return self.graph

    def add_nodes(self, workflow: StateGraph[RAGState]) -> None:
        """Add all nodes to workflow."""
        workflow.add_node("retrieve", self._nodes.retrieve)
        workflow.add_node("grade_documents", self._nodes.grade_documents)
        workflow.add_node("transform_query", self._nodes.transform_query)
        workflow.add_node("generate", self._nodes.generate)
        workflow.add_node("check_hallucination", self._nodes.check_hallucination)
        workflow.add_node("check_answer", self._nodes.check_answer)
        workflow.add_node("web_search", self._nodes.web_search)

    def add_edges(self, workflow: StateGraph[RAGState]) -> None:
        """Add edges and conditional routing."""
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self.route_after_grading,
            {
                "generate": "generate",
                "transform_query": "transform_query",
                "web_search": "web_search",
            },
        )
        workflow.add_edge("transform_query", "retrieve")
        workflow.add_edge("web_search", "generate")
        workflow.add_edge("generate", "check_hallucination")
        workflow.add_conditional_edges(
            "check_hallucination",
            self.route_after_hallucination_check,
            {"check_answer": "check_answer", "generate": "generate"},
        )
        workflow.add_conditional_edges(
            "check_answer",
            self.route_after_answer_check,
            {"end": END, "transform_query": "transform_query"},
        )

    def route_after_grading(
        self, state: RAGState
    ) -> Literal["generate", "transform_query", "web_search"]:
        """Route based on document relevance."""
        if state.get("documents_relevant"):
            return "generate"
        if state["retrieval_attempts"] >= state["max_retrieval_attempts"]:
            return "web_search"
        return "transform_query"

    def route_after_hallucination_check(
        self, state: RAGState
    ) -> Literal["check_answer", "generate"]:
        """Route based on hallucination detection."""
        return "generate" if state.get("hallucination_detected") else "check_answer"

    def route_after_answer_check(self, state: RAGState) -> Literal["end", "transform_query"]:
        """Route based on answer usefulness."""
        if state.get("answer_useful"):
            return "end"
        if state["retrieval_attempts"] >= state["max_retrieval_attempts"]:
            return "end"
        return "transform_query"

    async def run(self, question: str, max_attempts: int = 3) -> str:
        """Execute RAG workflow and return answer."""
        if self.graph is None:
            self.build()
        initial_state: RAGState = {
            "question": question,
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": max_attempts,
        }
        assert self.graph is not None
        final_state = await self.graph.ainvoke(initial_state)
        return final_state.get("generation", "")
