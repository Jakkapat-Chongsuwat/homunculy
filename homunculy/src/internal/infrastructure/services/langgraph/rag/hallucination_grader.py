"""Hallucination Grader Implementation."""

from typing import List, Dict, Any

from internal.domain.services import HallucinationGraderService, LLMClient
from .schemas import GradeHallucinationsSchema

HALLUCINATION_GRADER_PROMPT = """You are a grader assessing whether an LLM generation is grounded.
Give a binary score 'yes' or 'no'. 'Yes' means grounded, 'no' means hallucination."""


class OpenAIHallucinationGrader(HallucinationGraderService):
    """OpenAI implementation of hallucination grader."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize with LLM client."""
        self._client = llm_client

    async def check(self, documents: List[Dict[str, Any]], generation: str) -> bool:
        """Check if generation is grounded in documents."""
        docs_text = self._format_documents(documents)
        messages = self._build_messages(docs_text, generation)
        result = await self._client.invoke_structured(messages, GradeHallucinationsSchema)
        return self._parse_result(result)

    def _format_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents for prompt."""
        return "\n\n".join(doc.get("content", "") for doc in documents)

    def _build_messages(self, docs_text: str, generation: str) -> List[Dict[str, str]]:
        """Build prompt messages."""
        return [
            {"role": "system", "content": HALLUCINATION_GRADER_PROMPT},
            {"role": "user", "content": f"Documents:\n{docs_text}\n\nGeneration: {generation}"},
        ]

    def _parse_result(self, result: GradeHallucinationsSchema) -> bool:
        """Parse grading result."""
        return result.binary_score.lower() == "yes"
