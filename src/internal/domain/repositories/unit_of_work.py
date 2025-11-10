"""
Unit of Work Interface.

Defines the contract for managing transactions across multiple repositories.
The UoW coordinates multiple repositories in a single transaction, ensuring
all changes are committed or rolled back together atomically.

Key Principles:
- Repositories NEVER call each other directly
- Use Cases orchestrate multiple repositories through UoW
- UoW ensures transaction consistency across all repositories
- Each repository focuses on its single entity type
"""

from abc import ABC, abstractmethod

from .agent_repository import AgentRepository


class UnitOfWork(ABC):
    """
    Abstract Unit of Work.
    
    Manages transactions and coordinates changes across multiple repositories.
    Repositories are accessed as properties and share the same transaction context.
    
    Usage Example:
        async with uow:
            # All repository calls share the same transaction
            agent = await uow.agents.create(agent_data)
            await uow.memories.create(agent.id, memory_data)
            
            # Commit all changes together atomically
            await uow.commit()
            
            # If error occurs, all changes are rolled back
    """
    
    # Repository properties - add more as needed
    agents: AgentRepository
    # Future repositories:
    # memories: MemoryRepository
    # conversations: ConversationRepository
    # configurations: ConfigurationRepository
    
    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Enter async context manager - start transaction."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit async context manager.
        
        Automatically commits if no exception, rolls back if exception occurred.
        """
        pass
    
    @abstractmethod
    async def commit(self):
        """
        Commit the current transaction.
        
        All changes made through all repositories are persisted atomically.
        """
        pass
    
    @abstractmethod
    async def rollback(self):
        """
        Rollback the current transaction.
        
        All changes made through all repositories are discarded.
        """
        pass
