"""Document and Answer Graders."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


class GradeDocuments(BaseModel):
    """Binary score for document relevance."""

    binary_score: str = Field(description="Documents are relevant: 'yes' or 'no'")


class GradeHallucinations(BaseModel):
    """Binary score for hallucination detection."""

    binary_score: str = Field(description="Answer is grounded in facts: 'yes' or 'no'")


class GradeAnswer(BaseModel):
    """Binary score for answer usefulness."""

    binary_score: str = Field(description="Answer addresses the question: 'yes' or 'no'")


class DocumentGrader:
    """Grades document relevance to a question."""

    SYSTEM_PROMPT = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keywords or semantic meaning related to the question, grade it as relevant.
Give a binary score 'yes' or 'no' to indicate relevance."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """Initialize document grader."""
        llm = ChatOpenAI(model=model, temperature=0)
        self._grader = llm.with_structured_output(GradeDocuments)

    async def grade(self, question: str, document: str) -> bool:
        """Grade single document relevance."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Document:\n{document}\n\nQuestion: {question}",
            },
        ]
        result = await self._grader.ainvoke(messages)
        return result.binary_score.lower() == "yes"

    async def grade_documents(
        self,
        question: str,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter documents by relevance."""
        relevant = []
        for doc in documents:
            content = doc.get("content", "")
            if await self.grade(question, content):
                relevant.append(doc)
        return relevant


class HallucinationGrader:
    """Detects hallucinations in generated answers."""

    SYSTEM_PROMPT = """You are a grader assessing whether an LLM generation is grounded in retrieved documents.
Give a binary score 'yes' or 'no'. 'Yes' means the generation is grounded, 'no' means it contains hallucinations."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """Initialize hallucination grader."""
        llm = ChatOpenAI(model=model, temperature=0)
        self._grader = llm.with_structured_output(GradeHallucinations)

    async def check(
        self,
        documents: List[Dict[str, Any]],
        generation: str,
    ) -> bool:
        """Check if generation is grounded in documents.

        Returns:
            True if grounded (no hallucination), False otherwise.
        """
        docs_text = self._format_documents(documents)
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Documents:\n{docs_text}\n\nGeneration: {generation}",
            },
        ]
        result = await self._grader.ainvoke(messages)
        return result.binary_score.lower() == "yes"

    def _format_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents for prompt."""
        return "\n\n".join(doc.get("content", "") for doc in documents)


class AnswerGrader:
    """Grades if answer addresses the question."""

    SYSTEM_PROMPT = """You are a grader assessing whether an answer addresses the user question.
Give a binary score 'yes' or 'no'. 'Yes' means the answer is useful and addresses the question."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """Initialize answer grader."""
        llm = ChatOpenAI(model=model, temperature=0)
        self._grader = llm.with_structured_output(GradeAnswer)

    async def grade(self, question: str, generation: str) -> bool:
        """Grade if answer addresses question."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nAnswer: {generation}",
            },
        ]
        result = await self._grader.ainvoke(messages)
        return result.binary_score.lower() == "yes"
