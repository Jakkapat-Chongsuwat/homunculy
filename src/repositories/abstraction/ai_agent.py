"""
Abstract AI Agent Repository Interface.

This module defines the abstract repository interface for AI agents,
following the repository pattern established in the Pokemon system.
AI agents combine both data persistence AND execution logic in repositories.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional

from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
    AgentThread,
)


class AbstractAIAgentRepository(ABC):
    """Abstract repository interface for AI agents."""

    @abstractmethod
    async def save_agent_config(self, config: AgentConfiguration) -> str:
        """Save agent configuration and return agent ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_agent_config(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID."""
        raise NotImplementedError

    @abstractmethod
    async def update_agent_config(self, agent_id: str, config: AgentConfiguration) -> bool:
        """Update agent configuration."""
        raise NotImplementedError

    @abstractmethod
    async def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration."""
        raise NotImplementedError

    @abstractmethod
    async def list_agent_configs(self, limit: int = 50, offset: int = 0) -> List[AgentConfiguration]:
        """List all agent configurations."""
        raise NotImplementedError

    @abstractmethod
    async def save_thread(self, thread: AgentThread) -> str:
        """Save conversation thread and return thread ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Optional[AgentThread]:
        """Get conversation thread by ID."""
        raise NotImplementedError

    @abstractmethod
    async def update_thread(self, thread: AgentThread) -> bool:
        """Update conversation thread."""
        raise NotImplementedError

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete conversation thread."""
        raise NotImplementedError

    @abstractmethod
    async def list_threads_by_agent(
        self, agent_id: str, limit: int = 50, offset: int = 0
    ) -> List[AgentThread]:
        """List conversation threads for a specific agent."""
        raise NotImplementedError

    @abstractmethod
    async def save_personality(self, personality: AgentPersonality) -> str:
        """Save agent personality and return personality ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_personality(self, personality_id: str) -> Optional[AgentPersonality]:
        """Get agent personality by ID."""
        raise NotImplementedError

    @abstractmethod
    async def update_personality(self, personality_id: str, personality: AgentPersonality) -> bool:
        """Update agent personality."""
        raise NotImplementedError

    @abstractmethod
    async def delete_personality(self, personality_id: str) -> bool:
        """Delete agent personality."""
        raise NotImplementedError

    # AI Execution Methods (following Pokemon pattern where repos handle business logic)
    @abstractmethod
    async def initialize_agent(self, config: AgentConfiguration) -> str:
        """Initialize an AI agent with the given configuration."""
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        agent_id: str,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> AgentResponse:
        """Send a message to an agent and get response."""
        raise NotImplementedError

    @abstractmethod
    def chat_stream(
        self,
        agent_id: str,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> AsyncIterator[AgentResponse]:
        """Send a message to an agent and get streaming response."""
        raise NotImplementedError

    @abstractmethod
    async def update_agent_personality(
        self,
        agent_id: str,
        personality: AgentPersonality,
    ) -> bool:
        """Update agent's personality traits."""
        raise NotImplementedError

    @abstractmethod
    async def get_thread_history(self, thread_id: str) -> List[AgentMessage]:
        """Get conversation history for a thread."""
        raise NotImplementedError

    @abstractmethod
    async def clear_thread_history(self, thread_id: str) -> bool:
        """Clear conversation history for a thread."""
        raise NotImplementedError

    @abstractmethod
    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status of an agent."""
        raise NotImplementedError

    @abstractmethod
    async def shutdown_agent(self, agent_id: str) -> bool:
        """Shutdown a specific agent."""
        raise NotImplementedError

    @abstractmethod
    async def list_available_providers(self) -> List[AgentProvider]:
        """List all available AI agent providers."""
        raise NotImplementedError