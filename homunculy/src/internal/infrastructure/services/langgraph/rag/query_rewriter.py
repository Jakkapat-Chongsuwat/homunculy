"""Query Rewriter Implementation."""

from typing import List, Dict

from internal.domain.services import QueryRewriterService, LLMClient

QUERY_REWRITER_PROMPT = """You are a question re-writer. Convert the input question 
to a better version optimized for vectorstore retrieval. 
Output only the rewritten question."""


class OpenAIQueryRewriter(QueryRewriterService):
    """OpenAI implementation of query rewriter."""

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize with LLM client."""
        self._client = llm_client

    async def rewrite(self, question: str) -> str:
        """Rewrite question for better retrieval."""
        messages = self._build_messages(question)
        return await self._client.invoke(messages)

    def _build_messages(self, question: str) -> List[Dict[str, str]]:
        """Build prompt messages."""
        return [
            {"role": "system", "content": QUERY_REWRITER_PROMPT},
            {"role": "user", "content": question},
        ]
