"""Unit of Work contract."""

from abc import ABC, abstractmethod

from .agent_repository import AgentRepository


class UnitOfWork(ABC):
    """Transaction boundary for repositories."""

    agents: AgentRepository
    # Future repositories:
    # memories: MemoryRepository
    # conversations: ConversationRepository
    # configurations: ConfigurationRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Enter transaction context."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        pass

    @abstractmethod
    async def commit(self):
        """Commit transaction."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback transaction."""
        pass
