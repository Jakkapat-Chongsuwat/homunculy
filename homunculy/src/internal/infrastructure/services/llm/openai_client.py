"""OpenAI LLM Client Implementation."""

from typing import Any, List, Dict, Type, TypeVar, cast
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from internal.domain.services import LLMClient

T = TypeVar("T", bound=BaseModel)


class OpenAILLMClient(LLMClient):
    """OpenAI implementation of LLM client."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0) -> None:
        """Initialize OpenAI client."""
        self._llm = ChatOpenAI(model=model, temperature=temperature)

    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM and return text response."""
        response = await self._llm.ainvoke(messages)
        content = response.content
        if isinstance(content, str):
            return content
        return str(content)

    async def invoke_structured(self, messages: List[Dict[str, str]], schema: Type[T]) -> T:
        """Invoke LLM with structured output."""
        structured_llm = self._llm.with_structured_output(schema)
        result = await structured_llm.ainvoke(messages)
        return cast(T, result)


def create_openai_client(model: str = "gpt-4o-mini", temperature: float = 0) -> LLMClient:
    """Factory function to create OpenAI client."""
    return OpenAILLMClient(model=model, temperature=temperature)
