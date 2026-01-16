"""Unit tests for self-reflective RAG graph."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from internal.infrastructure.services.langgraph.rag.graph import SelfReflectiveRAGGraph
from internal.infrastructure.services.langgraph.rag.nodes import RAGNodes
from internal.infrastructure.services.langgraph.rag.state import RAGState


class TestSelfReflectiveRAGGraph:
    """Tests for SelfReflectiveRAGGraph."""

    @pytest.fixture
    def mock_nodes(self) -> MagicMock:
        """Create mock RAG nodes."""
        nodes = MagicMock(spec=RAGNodes)
        nodes.retrieve = AsyncMock()
        nodes.grade_documents = AsyncMock()
        nodes.transform_query = AsyncMock()
        nodes.generate = AsyncMock()
        nodes.check_hallucination = AsyncMock()
        nodes.check_answer = AsyncMock()
        nodes.web_search = AsyncMock()
        return nodes

    @pytest.fixture
    def graph(self, mock_nodes: MagicMock) -> SelfReflectiveRAGGraph:
        """Create graph with mocked nodes."""
        return SelfReflectiveRAGGraph(mock_nodes)

    def test_build_creates_graph(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should build and compile graph."""
        result = graph.build()
        assert result is not None
        assert graph.graph is not None

    def test_route_after_grading_returns_generate(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should route to generate when documents relevant."""
        state: RAGState = {
            "question": "test",
            "documents": [{"content": "relevant"}],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
            "documents_relevant": True,
        }
        assert graph.route_after_grading(state) == "generate"

    def test_route_after_grading_returns_transform_query(
        self, graph: SelfReflectiveRAGGraph
    ) -> None:
        """Should route to transform_query when not relevant."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
            "documents_relevant": False,
        }
        assert graph.route_after_grading(state) == "transform_query"

    def test_route_after_grading_returns_web_search(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should route to web_search when max attempts reached."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "",
            "retrieval_attempts": 3,
            "max_retrieval_attempts": 3,
            "documents_relevant": False,
        }
        assert graph.route_after_grading(state) == "web_search"

    def test_route_after_hallucination_check_to_answer(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should route to check_answer when no hallucination."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "answer",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
            "hallucination_detected": False,
        }
        assert graph.route_after_hallucination_check(state) == "check_answer"

    def test_route_after_hallucination_check_regenerate(
        self, graph: SelfReflectiveRAGGraph
    ) -> None:
        """Should route to generate when hallucination detected."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "bad answer",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
            "hallucination_detected": True,
        }
        assert graph.route_after_hallucination_check(state) == "generate"

    def test_route_after_answer_check_to_end(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should route to end when answer is useful."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "good answer",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
            "answer_useful": True,
        }
        assert graph.route_after_answer_check(state) == "end"

    def test_route_after_answer_check_to_transform(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should route to transform_query when answer not useful."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "bad answer",
            "retrieval_attempts": 1,
            "max_retrieval_attempts": 3,
            "answer_useful": False,
        }
        assert graph.route_after_answer_check(state) == "transform_query"

    def test_route_after_answer_check_to_end_on_max_attempts(
        self, graph: SelfReflectiveRAGGraph
    ) -> None:
        """Should route to end when max attempts reached."""
        state: RAGState = {
            "question": "test",
            "documents": [],
            "generation": "answer",
            "retrieval_attempts": 3,
            "max_retrieval_attempts": 3,
            "answer_useful": False,
        }
        assert graph.route_after_answer_check(state) == "end"

    @pytest.mark.asyncio
    async def test_run_executes_workflow(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should execute full workflow and return answer."""
        graph.build()
        graph.graph.ainvoke = AsyncMock(  # type: ignore
            return_value={"generation": "Python is a programming language."}
        )
        result = await graph.run("What is Python?")
        assert result == "Python is a programming language."

    @pytest.mark.asyncio
    async def test_run_builds_graph_if_not_built(self, graph: SelfReflectiveRAGGraph) -> None:
        """Should build graph on first run if not built."""
        assert graph.graph is None
        graph.build()
        graph.graph.ainvoke = AsyncMock(return_value={"generation": "answer"})  # type: ignore
        await graph.run("test question")
        assert graph.graph is not None


class TestGraphNodeRegistration:
    """Tests for graph node registration."""

    @pytest.fixture
    def mock_nodes(self) -> MagicMock:
        """Create mock RAG nodes."""
        return MagicMock(spec=RAGNodes)

    def test_add_nodes_registers_all_nodes(self, mock_nodes: MagicMock) -> None:
        """Should register all required nodes."""
        graph = SelfReflectiveRAGGraph(mock_nodes)
        mock_workflow = MagicMock()
        graph.add_nodes(mock_workflow)
        assert mock_workflow.add_node.call_count == 7

    def test_add_edges_sets_entry_point(self, mock_nodes: MagicMock) -> None:
        """Should set retrieve as entry point."""
        graph = SelfReflectiveRAGGraph(mock_nodes)
        mock_workflow = MagicMock()
        graph.add_edges(mock_workflow)
        mock_workflow.set_entry_point.assert_called_once_with("retrieve")
