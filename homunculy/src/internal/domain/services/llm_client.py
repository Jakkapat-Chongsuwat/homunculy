"""LLM client contract."""

from abc import ABC, abstractmethod
from typing import Dict, List, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """LLM operations contract."""

    @abstractmethod
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM with messages."""

    @abstractmethod
    async def invoke_structured(self, messages: List[Dict[str, str]], schema: Type[T]) -> T:
        """Invoke LLM with structured output."""
