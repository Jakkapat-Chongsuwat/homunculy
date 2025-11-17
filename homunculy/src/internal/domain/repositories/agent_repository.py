"""
Agent Repository Interface.

This module defines the repository interface for Agent persistence operations.
Following the Repository pattern, this interface is part of the domain layer
and implementations belong to the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from internal.domain.entities import Agent, AgentConfiguration


class AgentRepository(ABC):
    """Repository interface for Agent persistence operations."""

    @abstractmethod
    async def create(self, agent: Agent) -> Agent:
        """
        Create a new agent.
        
        Args:
            agent: The agent entity to create
            
        Returns:
            The created agent with generated ID
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Retrieve an agent by ID.
        
        Args:
            agent_id: The agent's unique identifier
            
        Returns:
            The agent entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        """
        Update an existing agent.
        
        Args:
            agent: The agent entity with updated data
            
        Returns:
            The updated agent entity
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """
        Delete an agent by ID.
        
        Args:
            agent_id: The agent's unique identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        """
        List all agents with pagination.
        
        Args:
            limit: Maximum number of agents to return
            offset: Number of agents to skip
            
        Returns:
            List of agent entities
        """
        raise NotImplementedError

    @abstractmethod
    async def update_configuration(
        self, agent_id: str, configuration: AgentConfiguration
    ) -> bool:
        """
        Update an agent's configuration.
        
        Args:
            agent_id: The agent's unique identifier
            configuration: New configuration
            
        Returns:
            True if updated successfully, False otherwise
        """
        raise NotImplementedError
