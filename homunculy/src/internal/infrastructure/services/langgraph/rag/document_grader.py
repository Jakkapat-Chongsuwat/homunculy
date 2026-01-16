"""Document Grader Implementation."""

from typing import Any, Dict, List

from internal.domain.services import DocumentGraderService, LLMClient

from .schemas import GradeDocumentsSchema

DOCUMENT_GRADER_PROMPT = """You are a grader assessing relevance of a retrieved document.
If the document contains keywords or semantic meaning related to the question, grade relevant.
Give a binary score 'yes' or 'no' to indicate relevance."""


class OpenAIDocumentGrader(DocumentGraderService):
    """OpenAI implementation of document grader."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize with LLM client."""
        self._client = llm_client

    async def grade(self, question: str, document: str) -> bool:
        """Grade single document relevance."""
        messages = self._build_messages(question, document)
        result = await self._client.invoke_structured(messages, GradeDocumentsSchema)
        return self._parse_result(result)

    async def grade_batch(
        self, question: str, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter documents by relevance."""
        relevant = []
        for doc in documents:
            content = doc.get("content", "")
            if await self.grade(question, content):
                relevant.append(doc)
        return relevant

    def _build_messages(self, question: str, document: str) -> List[Dict[str, str]]:
        """Build prompt messages."""
        return [
            {"role": "system", "content": DOCUMENT_GRADER_PROMPT},
            {"role": "user", "content": f"Document:\n{document}\n\nQuestion: {question}"},
        ]

    def _parse_result(self, result: GradeDocumentsSchema) -> bool:
        """Parse grading result."""
        return result.binary_score.lower() == "yes"
