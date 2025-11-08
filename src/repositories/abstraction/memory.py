"""
Abstract Memory Repository Interface.

Defines the contract for memory storage operations following Clean Architecture.
This abstraction allows different memory providers (Mem0, custom DB, etc.) 
without coupling domain logic to specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryItem:
    """Domain model for a memory item."""
    
    id: str
    memory: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    score: Optional[float] = None  # Relevance score from search


@dataclass
class MemorySearchResult:
    """Result from memory search operation."""
    
    results: List[MemoryItem]
    total: int


class IMemoryRepository(ABC):
    """
    Abstract repository for memory operations.
    
    This interface follows the Repository Pattern and Dependency Inversion Principle,
    allowing the domain layer to remain independent of infrastructure concerns.
    """
    
    @abstractmethod
    async def add_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Add new memories from conversation messages.
        
        Args:
            messages: List of conversation messages with 'role' and 'content'
            user_id: Optional user identifier
            agent_id: Optional agent identifier  
            run_id: Optional session/run identifier
            metadata: Optional metadata to attach to memories
            
        Returns:
            List of created memory items
        """
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 5,
    ) -> MemorySearchResult:
        """
        Search for relevant memories based on query.
        
        Args:
            query: Search query
            user_id: Optional user filter
            agent_id: Optional agent filter
            run_id: Optional run filter
            limit: Maximum number of results
            
        Returns:
            Search results with relevance scores
        """
        pass
    
    @abstractmethod
    async def get_all_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve all memories matching filters.
        
        Args:
            user_id: Optional user filter
            agent_id: Optional agent filter
            run_id: Optional run filter
            
        Returns:
            List of matching memory items
        """
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        data: str,
    ) -> MemoryItem:
        """
        Update an existing memory.
        
        Args:
            memory_id: Memory identifier
            data: New memory content
            
        Returns:
            Updated memory item
        """
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def delete_all_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> int:
        """
        Delete all memories matching filters.
        
        Args:
            user_id: Optional user filter
            agent_id: Optional agent filter
            run_id: Optional run filter
            
        Returns:
            Number of memories deleted
        """
        pass
    
    @abstractmethod
    async def get_memory_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Get change history for a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            List of historical versions
        """
        pass
