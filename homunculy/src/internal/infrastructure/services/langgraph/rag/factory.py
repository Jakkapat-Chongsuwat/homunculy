"""RAG Graph Factory."""

from internal.domain.services import LLMClient, RAGService
from internal.infrastructure.services.llm import create_openai_client

from .answer_grader import OpenAIAnswerGrader
from .document_grader import OpenAIDocumentGrader
from .graph import SelfReflectiveRAGGraph
from .hallucination_grader import OpenAIHallucinationGrader
from .nodes import RAGNodes
from .query_rewriter import OpenAIQueryRewriter


def create_rag_graph(
    rag_service: RAGService,
    llm_client: LLMClient | None = None,
    model: str = "gpt-4o-mini",
) -> SelfReflectiveRAGGraph:
    """Factory to create self-reflective RAG graph with all dependencies."""
    client = llm_client or create_openai_client(model=model)

    nodes = RAGNodes(
        rag_service=rag_service,
        llm_client=client,
        doc_grader=OpenAIDocumentGrader(client),
        hallucination_grader=OpenAIHallucinationGrader(client),
        answer_grader=OpenAIAnswerGrader(client),
        query_rewriter=OpenAIQueryRewriter(client),
    )

    return SelfReflectiveRAGGraph(nodes)
