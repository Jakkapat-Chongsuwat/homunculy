"""
Repository interfaces for LLM operations.

This module defines the interfaces for LLM clients and factories
in the repository layer, following Clean Architecture principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from models.ai_agent.ai_agent import AgentConfiguration, AgentResponse


class ILLMClient(ABC):
    """Interface for LLM client implementations."""

    @abstractmethod
    def create_agent(self, agent_id: str, config: AgentConfiguration) -> None:
        """Create an LLM agent with the specified ID."""
        pass

    @abstractmethod
    async def chat(
        self,
        agent_id: str,
        message: str,
        context: Optional[Dict[str, str]] = None
    ) -> AgentResponse:
        """Send a message to an LLM agent and get response."""
        pass

    @abstractmethod
    def update_agent(self, agent_id: str, config: AgentConfiguration) -> None:
        """Update an existing LLM agent's configuration."""
        pass

    @abstractmethod
    def remove_agent(self, agent_id: str) -> None:
        """Remove an LLM agent."""
        pass


class ILLMFactory(ABC):
    """Interface for LLM factory implementations."""

    @abstractmethod
    def create_client(self, provider: str) -> ILLMClient:
        """Create an LLM client for the specified provider."""
        pass

    @abstractmethod
    def get_supported_providers(self) -> list[str]:
        """Get list of supported LLM providers."""
        pass