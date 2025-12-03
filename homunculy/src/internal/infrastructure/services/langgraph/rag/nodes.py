"""RAG Graph Nodes."""

from typing import Dict, Any, List

from internal.domain.services import (
    RAGService,
    LLMClient,
    DocumentGraderService,
    HallucinationGraderService,
    AnswerGraderService,
    QueryRewriterService,
)
from .state import RAGState

GENERATION_PROMPT = """You are an assistant for question-answering tasks.
Use the context to answer the question. If you don't know, say so. Be concise."""


class RAGNodes:
    """Nodes for self-reflective RAG workflow."""

    def __init__(
        self,
        rag_service: RAGService,
        llm_client: LLMClient,
        doc_grader: DocumentGraderService,
        hallucination_grader: HallucinationGraderService,
        answer_grader: AnswerGraderService,
        query_rewriter: QueryRewriterService,
    ) -> None:
        """Initialize RAG nodes with injected dependencies."""
        self._rag = rag_service
        self._llm = llm_client
        self._doc_grader = doc_grader
        self._hallucination_grader = hallucination_grader
        self._answer_grader = answer_grader
        self._query_rewriter = query_rewriter

    async def retrieve(self, state: RAGState) -> Dict[str, Any]:
        """Retrieve documents from vector store."""
        query = state.get("rewritten_query") or state["question"]
        documents = await self._rag.retrieve(query, top_k=5)
        return {"documents": documents, "retrieval_attempts": state["retrieval_attempts"] + 1}

    async def grade_documents(self, state: RAGState) -> Dict[str, Any]:
        """Grade document relevance."""
        relevant = await self._doc_grader.grade_batch(state["question"], state["documents"])
        has_relevant = len(relevant) > 0
        return {
            "documents": relevant if has_relevant else state["documents"],
            "documents_relevant": has_relevant,
            "web_search_needed": not has_relevant,
        }

    async def transform_query(self, state: RAGState) -> Dict[str, Any]:
        """Rewrite query for better retrieval."""
        rewritten = await self._query_rewriter.rewrite(state["question"])
        return {"rewritten_query": rewritten, "documents": []}

    async def generate(self, state: RAGState) -> Dict[str, Any]:
        """Generate answer from documents."""
        context = self.format_context(state["documents"])
        messages = self.build_prompt(state["question"], context)
        response = await self._llm.invoke(messages)
        return {"generation": response}

    async def check_hallucination(self, state: RAGState) -> Dict[str, Any]:
        """Check for hallucinations in generation."""
        is_grounded = await self._hallucination_grader.check(
            state["documents"], state["generation"]
        )
        return {"hallucination_detected": not is_grounded}

    async def check_answer(self, state: RAGState) -> Dict[str, Any]:
        """Check if answer addresses question."""
        is_useful = await self._answer_grader.grade(state["question"], state["generation"])
        return {"answer_useful": is_useful}

    async def web_search(self, state: RAGState) -> Dict[str, Any]:
        """Perform web search for additional context."""
        query = state.get("rewritten_query") or state["question"]
        return {"documents": await self._rag.search_web(query)}

    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents into context string."""
        return "\n\n".join(doc.get("content", "") for doc in documents)

    def build_prompt(self, question: str, context: str) -> List[Dict[str, str]]:
        """Build prompt for answer generation."""
        return [
            {"role": "system", "content": GENERATION_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
