"""
Domain Exceptions.

CLEAN ARCHITECTURE PRINCIPLE:
Domain layer exceptions should only represent pure business rule violations.
Domain knows NOTHING about infrastructure (databases, APIs, frameworks).

Infrastructure exceptions (like CheckpointerException) belong in infrastructure layer.
"""


class DomainException(Exception):
    """
    Base exception for all domain-level errors.
    
    Domain exceptions represent business rule violations, not technical failures.
    All custom exceptions in the domain layer should inherit from this.
    """
    
    def __init__(self, message: str, *args, **kwargs):
        """
        Initialize domain exception.
        
        Args:
            message: Human-readable error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments for context
        """
        self.message = message
        self.context = kwargs
        super().__init__(message, *args)
    
    def __str__(self) -> str:
        """String representation of the exception."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


# Agent Domain Exceptions (Business Rules)
class AgentException(DomainException):
    """Base exception for agent business rule violations."""
    pass


class AgentNotFoundException(AgentException):
    """Raised when an agent cannot be found (business rule: agent must exist)."""
    
    def __init__(self, agent_id: str):
        super().__init__("Agent not found", agent_id=agent_id)


class AgentConfigurationException(AgentException):
    """Raised when agent configuration violates business rules."""
    pass


class AgentExecutionException(AgentException):
    """Raised when agent execution violates business rules."""
    pass


# Repository Domain Exceptions (Persistence Abstraction)
class RepositoryException(DomainException):
    """Base exception for repository contract violations."""
    pass


class EntityNotFoundException(RepositoryException):
    """Raised when an entity cannot be found (domain concept)."""
    
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            f"{entity_type} not found",
            entity_type=entity_type,
            entity_id=entity_id
        )


class DuplicateEntityException(RepositoryException):
    """Raised when entity uniqueness constraint is violated."""
    
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            f"{entity_type} already exists",
            entity_type=entity_type,
            entity_id=entity_id
        )


# Validation Exceptions (Business Rules)
class ValidationException(DomainException):
    """Base exception for business validation errors."""
    
    def __init__(self, message: str, field: str | None = None, value=None):
        super().__init__(message, field=field, value=value)


class InvalidConfigurationException(ValidationException):
    """Raised when configuration violates business rules."""
    pass


class InvalidInputException(ValidationException):
    """Raised when input violates business rules."""
    pass


__all__ = [
    # Base
    "DomainException",
    # Agent
    "AgentException",
    "AgentNotFoundException",
    "AgentConfigurationException",
    "AgentExecutionException",
    # Repository
    "RepositoryException",
    "EntityNotFoundException",
    "DuplicateEntityException",
    # Validation
    "ValidationException",
    "InvalidConfigurationException",
    "InvalidInputException",
]
