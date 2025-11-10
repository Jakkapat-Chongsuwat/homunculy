"""
Agent Use Cases.

This module implements application-level business logic for agent operations.
Use cases coordinate between domain entities and repositories, following
Clean Architecture principles.

Note: These classes implicitly implement the Protocol interfaces from interfaces.py
through structural subtyping (no explicit inheritance needed).
"""

from typing import List, Optional

from internal.domain.entities import Agent, AgentConfiguration, AgentResponse
from internal.domain.repositories import AgentRepository


class CreateAgentUseCaseImpl:
    """Use case for creating a new agent."""
    
    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize the use case.
        
        Args:
            agent_repository: Repository for agent persistence
        """
        self.agent_repository = agent_repository
    
    async def execute(self, agent_id: str, name: str, configuration: AgentConfiguration) -> Agent:
        """
        Create a new agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Agent name
            configuration: Agent configuration
            
        Returns:
            The created agent entity
        """
        agent = Agent(
            id=agent_id,
            name=name,
            configuration=configuration,
        )
        
        return await self.agent_repository.create(agent)


class GetAgentUseCaseImpl:
    """Use case for retrieving an agent."""
    
    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize the use case.
        
        Args:
            agent_repository: Repository for agent persistence
        """
        self.agent_repository = agent_repository
    
    async def execute(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            The agent entity if found, None otherwise
        """
        return await self.agent_repository.get_by_id(agent_id)


class ListAgentsUseCaseImpl:
    """Use case for listing agents."""
    
    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize the use case.
        
        Args:
            agent_repository: Repository for agent persistence
        """
        self.agent_repository = agent_repository
    
    async def execute(self, limit: int = 50, offset: int = 0) -> List[Agent]:
        """
        List all agents with pagination.
        
        Args:
            limit: Maximum number of agents to return
            offset: Number of agents to skip
            
        Returns:
            List of agent entities
        """
        return await self.agent_repository.list_all(limit, offset)


class UpdateAgentUseCaseImpl:
    """Use case for updating an agent."""
    
    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize the use case.
        
        Args:
            agent_repository: Repository for agent persistence
        """
        self.agent_repository = agent_repository
    
    async def execute(self, agent: Agent) -> Agent:
        """
        Update an existing agent.
        
        Args:
            agent: The agent entity with updated data
            
        Returns:
            The updated agent entity
        """
        return await self.agent_repository.update(agent)


class DeleteAgentUseCaseImpl:
    """Use case for deleting an agent."""
    
    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize the use case.
        
        Args:
            agent_repository: Repository for agent persistence
        """
        self.agent_repository = agent_repository
    
    async def execute(self, agent_id: str) -> bool:
        """
        Delete an agent by ID.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return await self.agent_repository.delete(agent_id)


class ChatWithAgentUseCaseImpl:
    """Use case for chatting with an agent."""
    
    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize the use case.
        
        Args:
            agent_repository: Repository for agent operations
        """
        self.agent_repository = agent_repository
    
    async def execute(
        self, 
        agent_id: str, 
        message: str,
        context: Optional[dict] = None
    ) -> AgentResponse:
        """
        Send a message to an agent and get response.
        
        Args:
            agent_id: Unique identifier for the agent
            message: User message
            context: Optional context dictionary
            
        Returns:
            Agent response
        """
        # This is a simplified version - in a real implementation,
        # you would interact with an LLM service through the repository
        # or a separate service layer
        
        # For now, return a placeholder response
        return AgentResponse(
            message="Response from agent",
            confidence=0.9,
            reasoning="Processed through use case layer"
        )
