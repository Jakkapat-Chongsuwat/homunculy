"""
In-Memory Agent Repository Implementation.

This is a simple in-memory implementation of AgentRepository for development
and testing purposes. In production, you would use SQLAlchemy with PostgreSQL or SQLite.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone

from internal.domain.entities import Agent, AgentConfiguration
from internal.domain.repositories import AgentRepository


class MemoryAgentRepository(AgentRepository):
    """In-memory implementation of AgentRepository."""
    
    def __init__(self):
        """Initialize the repository with empty storage."""
        self._agents: Dict[str, Agent] = {}
    
    async def create(self, agent: Agent) -> Agent:
        """
        Create a new agent in memory.
        
        Args:
            agent: The agent entity to create
            
        Returns:
            The created agent
        """
        if agent.id in self._agents:
            raise ValueError(f"Agent with ID {agent.id} already exists")
        
        self._agents[agent.id] = agent
        return agent
    
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Retrieve an agent by ID.
        
        Args:
            agent_id: The agent's unique identifier
            
        Returns:
            The agent entity if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    async def update(self, agent: Agent) -> Agent:
        """
        Update an existing agent.
        
        Args:
            agent: The agent entity with updated data
            
        Returns:
            The updated agent entity
        """
        if agent.id not in self._agents:
            raise ValueError(f"Agent with ID {agent.id} not found")
        
        agent.updated_at = datetime.now(timezone.utc)
        self._agents[agent.id] = agent
        return agent
    
    async def delete(self, agent_id: str) -> bool:
        """
        Delete an agent by ID.
        
        Args:
            agent_id: The agent's unique identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False
    
    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        """
        List all agents with pagination.
        
        Args:
            limit: Maximum number of agents to return
            offset: Number of agents to skip
            
        Returns:
            List of agent entities
        """
        all_agents = list(self._agents.values())
        return all_agents[offset:offset + limit]
    
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
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        agent.configuration = configuration
        agent.updated_at = datetime.now(timezone.utc)
        return True
