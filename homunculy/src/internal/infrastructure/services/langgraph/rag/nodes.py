"""RAG Graph Nodes."""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI

from internal.domain.services import RAGService
from .state import RAGState
from .graders import DocumentGrader, HallucinationGrader, AnswerGrader
from .query_rewriter import QueryRewriter


class RAGNodes:
    """Nodes for self-reflective RAG workflow."""

    def __init__(
        self,
        rag_service: RAGService,
        model: str = "gpt-4o-mini",
    ) -> None:
        """Initialize RAG nodes."""
        self._rag_service = rag_service
        self._model = model
        self._llm = ChatOpenAI(model=model, temperature=0)
        self._doc_grader = DocumentGrader(model)
        self._hallucination_grader = HallucinationGrader(model)
        self._answer_grader = AnswerGrader(model)
        self._query_rewriter = QueryRewriter(model)

    async def retrieve(self, state: RAGState) -> Dict[str, Any]:
        """Retrieve documents from vector store."""
        query = state.get("rewritten_query") or state["question"]
        attempts = state.get("retrieval_attempts", 0) + 1

        documents = await self._rag_service.retrieve(query, top_k=5)

        return {
            "documents": documents,
            "retrieval_attempts": attempts,
        }

    async def grade_documents(self, state: RAGState) -> Dict[str, Any]:
        """Grade document relevance."""
        question = state["question"]
        documents = state.get("documents", [])

        relevant_docs = await self._doc_grader.grade_documents(question, documents)
        has_relevant = len(relevant_docs) > 0

        return {
            "documents": relevant_docs if has_relevant else documents,
            "documents_relevant": has_relevant,
            "web_search_needed": not has_relevant,
        }

    async def transform_query(self, state: RAGState) -> Dict[str, Any]:
        """Rewrite query for better retrieval."""
        question = state["question"]
        rewritten = await self._query_rewriter.rewrite(question)

        return {
            "rewritten_query": rewritten,
            "documents": [],  # Reset documents for new retrieval
        }

    async def generate(self, state: RAGState) -> Dict[str, Any]:
        """Generate answer from documents."""
        question = state["question"]
        documents = state.get("documents", [])

        context = self._format_context(documents)
        messages = self._build_generation_prompt(question, context)

        response = await self._llm.ainvoke(messages)

        return {"generation": response.content}

    async def check_hallucination(self, state: RAGState) -> Dict[str, Any]:
        """Check for hallucinations in generation."""
        documents = state.get("documents", [])
        generation = state.get("generation", "")

        is_grounded = await self._hallucination_grader.check(documents, generation)

        return {"hallucination_detected": not is_grounded}

    async def check_answer(self, state: RAGState) -> Dict[str, Any]:
        """Check if answer addresses question."""
        question = state["question"]
        generation = state.get("generation", "")

        is_useful = await self._answer_grader.grade(question, generation)

        return {"answer_useful": is_useful}

    async def web_search(self, state: RAGState) -> Dict[str, Any]:
        """Perform web search for additional context."""
        query = state.get("rewritten_query") or state["question"]
        web_docs = await self._rag_service.search_web(query)

        return {"documents": web_docs}

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents into context string."""
        return "\n\n".join(doc.get("content", "") for doc in documents)

    def _build_generation_prompt(
        self,
        question: str,
        context: str,
    ) -> List[Dict[str, str]]:
        """Build prompt for answer generation."""
        system = """You are an assistant for question-answering tasks.
Use the following context to answer the question. If you don't know
the answer, say you don't know. Keep the answer concise."""

        user = f"Context:\n{context}\n\nQuestion: {question}"

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
