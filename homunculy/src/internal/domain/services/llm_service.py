"""LLM service contract."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, Optional

from internal.domain.entities import AgentConfiguration, AgentResponse


class LLMService(ABC):
    """LLM interactions contract."""

    @abstractmethod
    async def chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Send one chat message."""
        pass

    @abstractmethod
    def stream_chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream chat response chunks."""
        pass
