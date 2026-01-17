"""LLM service port (interface)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from domain.entities import AgentConfiguration, AgentResponse


class LLMPort(ABC):
    """LLM interactions contract."""

    @abstractmethod
    async def chat(
        self,
        config: AgentConfiguration,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Send one chat message."""
        ...

    @abstractmethod
    def stream_chat(
        self,
        config: AgentConfiguration,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat response chunks."""
        ...
