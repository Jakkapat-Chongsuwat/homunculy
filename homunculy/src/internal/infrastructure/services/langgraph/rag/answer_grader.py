"""Answer Grader Implementation."""

from typing import Dict, List

from internal.domain.services import AnswerGraderService, LLMClient

from .schemas import GradeAnswerSchema

ANSWER_GRADER_PROMPT = """You are a grader assessing whether an answer addresses the question.
Give a binary score 'yes' or 'no'. 'Yes' means the answer is useful."""


class OpenAIAnswerGrader(AnswerGraderService):
    """OpenAI implementation of answer grader."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize with LLM client."""
        self._client = llm_client

    async def grade(self, question: str, generation: str) -> bool:
        """Grade if answer addresses question."""
        messages = self._build_messages(question, generation)
        result = await self._client.invoke_structured(messages, GradeAnswerSchema)
        return self._parse_result(result)

    def _build_messages(self, question: str, generation: str) -> List[Dict[str, str]]:
        """Build prompt messages."""
        return [
            {"role": "system", "content": ANSWER_GRADER_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nAnswer: {generation}"},
        ]

    def _parse_result(self, result: GradeAnswerSchema) -> bool:
        """Parse grading result."""
        return result.binary_score.lower() == "yes"
