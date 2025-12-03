"""LLM Client Interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Abstract interface for LLM operations."""

    @abstractmethod
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM with messages and return response."""

    @abstractmethod
    async def invoke_structured(self, messages: List[Dict[str, str]], schema: Type[T]) -> T:
        """Invoke LLM with structured output."""
