"""Self-Reflective RAG Graph."""

from typing import Literal
from langgraph.graph import StateGraph, END

from internal.domain.services import RAGService
from .state import RAGState
from .nodes import RAGNodes


class SelfReflectiveRAGGraph:
    """Builds self-reflective RAG workflow graph."""

    def __init__(
        self,
        rag_service: RAGService,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Initialize graph builder."""
        self._nodes = RAGNodes(rag_service, model)
        self._graph = None

    def build(self) -> StateGraph:
        """Build the self-reflective RAG graph."""
        workflow = StateGraph(RAGState)

        self._add_nodes(workflow)
        self._add_edges(workflow)

        self._graph = workflow.compile()
        return self._graph

    def _add_nodes(self, workflow: StateGraph) -> None:
        """Add all nodes to workflow."""
        workflow.add_node("retrieve", self._nodes.retrieve)
        workflow.add_node("grade_documents", self._nodes.grade_documents)
        workflow.add_node("transform_query", self._nodes.transform_query)
        workflow.add_node("generate", self._nodes.generate)
        workflow.add_node("check_hallucination", self._nodes.check_hallucination)
        workflow.add_node("check_answer", self._nodes.check_answer)
        workflow.add_node("web_search", self._nodes.web_search)

    def _add_edges(self, workflow: StateGraph) -> None:
        """Add edges and conditional routing."""
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")

        workflow.add_conditional_edges(
            "grade_documents",
            self._route_after_grading,
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
            self._route_after_hallucination_check,
            {
                "check_answer": "check_answer",
                "generate": "generate",
            },
        )

        workflow.add_conditional_edges(
            "check_answer",
            self._route_after_answer_check,
            {
                "end": END,
                "transform_query": "transform_query",
            },
        )

    def _route_after_grading(
        self,
        state: RAGState,
    ) -> Literal["generate", "transform_query", "web_search"]:
        """Route based on document relevance."""
        if state.get("documents_relevant"):
            return "generate"

        attempts = state.get("retrieval_attempts", 0)
        max_attempts = state.get("max_retrieval_attempts", 3)

        if attempts >= max_attempts:
            return "web_search"

        return "transform_query"

    def _route_after_hallucination_check(
        self,
        state: RAGState,
    ) -> Literal["check_answer", "generate"]:
        """Route based on hallucination detection."""
        if state.get("hallucination_detected"):
            return "generate"
        return "check_answer"

    def _route_after_answer_check(
        self,
        state: RAGState,
    ) -> Literal["end", "transform_query"]:
        """Route based on answer usefulness."""
        if state.get("answer_useful"):
            return "end"

        attempts = state.get("retrieval_attempts", 0)
        max_attempts = state.get("max_retrieval_attempts", 3)

        if attempts >= max_attempts:
            return "end"

        return "transform_query"

    async def run(self, question: str) -> str:
        """Execute RAG workflow and return answer."""
        if self._graph is None:
            self.build()

        initial_state = {
            "question": question,
            "documents": [],
            "generation": "",
            "retrieval_attempts": 0,
            "max_retrieval_attempts": 3,
        }

        final_state = await self._graph.ainvoke(initial_state)
        return final_state.get("generation", "")
