"""
Abstract Waifu Repository Interface.

This module defines the repository abstraction for Waifu entities
and their relationships, following the Repository Pattern and
Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from models.ai_agent.waifu import Waifu, Relationship, Interaction


class AbstractWaifuRepository(ABC):
    """Abstract repository interface for Waifu domain entities."""

    # Waifu CRUD operations
    @abstractmethod
    async def initialize_agent(self, llm_factory, waifu_id: str, config) -> None:
        """
        Initialize the LLM agent for a waifu.
        
        This is a repository responsibility as it deals with infrastructure
        (LLM service initialization), not business logic.
        
        Args:
            llm_factory: Factory for creating LLM clients
            waifu_id: Waifu identifier
            config: Agent configuration
        """
        raise NotImplementedError

    @abstractmethod
    async def save_waifu(self, waifu: Waifu) -> str:
        """
        Save a waifu entity.
        
        Args:
            waifu: Waifu entity to save
            
        Returns:
            Waifu ID
        """
        raise NotImplementedError

    @abstractmethod
    async def get_waifu(self, waifu_id: str) -> Optional[Waifu]:
        """
        Get a waifu by ID.
        
        Args:
            waifu_id: Waifu identifier
            
        Returns:
            Waifu entity or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def update_waifu(self, waifu: Waifu) -> bool:
        """
        Update a waifu entity.
        
        Args:
            waifu: Waifu entity with updated data
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_waifu(self, waifu_id: str) -> bool:
        """
        Delete a waifu by ID.
        
        Args:
            waifu_id: Waifu identifier
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def list_waifus(self, limit: int = 50, offset: int = 0) -> List[Waifu]:
        """
        List all waifus with pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Waifu entities
        """
        raise NotImplementedError

    # Relationship CRUD operations
    @abstractmethod
    async def save_relationship(self, relationship: Relationship) -> str:
        """
        Save a relationship entity.
        
        Args:
            relationship: Relationship entity to save
            
        Returns:
            Relationship composite ID (user_id + waifu_id)
        """
        raise NotImplementedError

    @abstractmethod
    async def get_relationship(
        self, user_id: str, waifu_id: str
    ) -> Optional[Relationship]:
        """
        Get a relationship by user and waifu IDs.
        
        Args:
            user_id: User identifier
            waifu_id: Waifu identifier
            
        Returns:
            Relationship entity or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def update_relationship(self, relationship: Relationship) -> bool:
        """
        Update a relationship entity.
        
        Args:
            relationship: Relationship entity with updated data
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_relationship(self, user_id: str, waifu_id: str) -> bool:
        """
        Delete a relationship.
        
        Args:
            user_id: User identifier
            waifu_id: Waifu identifier
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def list_user_relationships(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Relationship]:
        """
        List all relationships for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Relationship entities
        """
        raise NotImplementedError

    @abstractmethod
    async def list_waifu_relationships(
        self, waifu_id: str, limit: int = 50, offset: int = 0
    ) -> List[Relationship]:
        """
        List all relationships for a waifu.
        
        Args:
            waifu_id: Waifu identifier
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Relationship entities
        """
        raise NotImplementedError

    # Interaction operations
    @abstractmethod
    async def save_interaction(
        self, user_id: str, waifu_id: str, interaction: Interaction
    ) -> str:
        """
        Save an interaction to a relationship.
        
        Args:
            user_id: User identifier
            waifu_id: Waifu identifier
            interaction: Interaction entity to save
            
        Returns:
            Interaction ID
        """
        raise NotImplementedError

    @abstractmethod
    async def get_interaction_history(
        self, user_id: str, waifu_id: str, limit: int = 100, offset: int = 0
    ) -> List[Interaction]:
        """
        Get interaction history for a relationship.
        
        Args:
            user_id: User identifier
            waifu_id: Waifu identifier
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Interaction entities
        """
        raise NotImplementedError

    # Agent interaction operations (infrastructure concerns)
    @abstractmethod
    async def chat_with_agent(self, llm_factory, agent_id: str, message: str, context: dict):
        """
        Chat with a waifu agent.
        
        This is infrastructure responsibility - delegates to the appropriate
        LLM provider without exposing implementation details to use cases.
        
        Args:
            llm_factory: Factory for creating LLM clients
            agent_id: Agent identifier
            message: User message
            context: Conversation context
            
        Returns:
            AgentResponse from the LLM
        """
        raise NotImplementedError

    @abstractmethod
    def chat_stream_with_agent(self, llm_factory, agent_id: str, message: str, context: dict):
        """
        Stream chat responses from a waifu agent.
        
        Args:
            llm_factory: Factory for creating LLM clients
            agent_id: Agent identifier
            message: User message
            context: Conversation context
            
        Yields:
            AgentResponse chunks from the LLM
        """
        raise NotImplementedError

    @abstractmethod
    async def update_agent_configuration(self, llm_factory, agent_id: str, config) -> None:
        """
        Update agent configuration.
        
        Args:
            llm_factory: Factory for creating LLM clients
            agent_id: Agent identifier
            config: New configuration
        """
        raise NotImplementedError
