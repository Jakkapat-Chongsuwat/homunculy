"""
LLM Service Interface.

Domain-level abstraction for Large Language Model interactions.
This belongs in the domain layer as it defines a contract that
infrastructure implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from internal.domain.entities import AgentResponse, AgentConfiguration


class LLMService(ABC):
    """
    Abstract interface for LLM service interactions.
    
    This interface allows the use case layer to depend on an abstraction
    rather than concrete implementations, following the Dependency Inversion Principle.
    """
    
    @abstractmethod
    async def chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Send a chat message using the configured LLM.
        
        Args:
            configuration: Agent configuration including model, temperature, etc.
            message: User message to send
            context: Optional conversation context
            
        Returns:
            AgentResponse with the LLM's reply
        """
        pass
