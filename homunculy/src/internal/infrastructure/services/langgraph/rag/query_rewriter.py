"""Query Rewriter for RAG."""

from langchain_openai import ChatOpenAI


class QueryRewriter:
    """Rewrites queries for better retrieval."""

    SYSTEM_PROMPT = """You are a question re-writer. Your task is to convert an input question 
to a better version optimized for vectorstore retrieval. Look at the input and try to 
reason about the underlying semantic intent / meaning. Output only the rewritten question."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        """Initialize query rewriter."""
        self._llm = ChatOpenAI(model=model, temperature=0)

    async def rewrite(self, question: str) -> str:
        """Rewrite question for better retrieval."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        response = await self._llm.ainvoke(messages)
        return response.content
