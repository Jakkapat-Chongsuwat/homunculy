"""
LangGraph Service Implementation.

Implements LLMService using LangGraph framework for agent orchestration.

Modular components:
- agent_service: Main service (refactored, ~200 lines)
- checkpointer_manager: Checkpoint lifecycle
- graph_manager: Graph caching and building
- response_builder: Response construction
- background_summarizer: Async summarization
- rag/: Self-reflective RAG with document grading
"""

from .agent_service import LangGraphAgentService
from .background_summarizer import BackgroundSummarizer, create_background_summarizer
from .checkpointer_manager import CheckpointerManager, create_checkpointer_manager
from .exceptions import (
    CheckpointerConnectionException,
    CheckpointerSetupException,
)
from .graph_manager import GraphManager, ThreadResolver, create_graph_manager
from .rag import (
    RAGState,
    SelfReflectiveRAGGraph,
    RAGNodes,
    DocumentGrader,
    HallucinationGrader,
    AnswerGrader,
)
from .response_builder import ResponseBuilder, create_response_builder

__all__ = [
    # Main service
    "LangGraphAgentService",
    # Modular components
    "BackgroundSummarizer",
    "create_background_summarizer",
    "CheckpointerManager",
    "create_checkpointer_manager",
    "GraphManager",
    "ThreadResolver",
    "create_graph_manager",
    "ResponseBuilder",
    "create_response_builder",
    # RAG components
    "RAGState",
    "SelfReflectiveRAGGraph",
    "RAGNodes",
    "DocumentGrader",
    "HallucinationGrader",
    "AnswerGrader",
    # Exceptions
    "CheckpointerConnectionException",
    "CheckpointerSetupException",
]
