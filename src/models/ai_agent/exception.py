"""
AI Agent Domain Exceptions.

This module defines exceptions specific to AI agent operations,
following the Clean Architecture pattern like Pokemon exceptions.
"""


class AIAgentError(Exception):
    """Base exception for AI agent related errors."""
    pass


class AgentNotFound(AIAgentError):
    """Raised when an agent configuration is not found."""
    pass


class AgentInitializationError(AIAgentError):
    """Raised when agent initialization fails."""
    pass


class AgentExecutionError(AIAgentError):
    """Raised when agent execution fails."""
    pass


class AgentConfigurationError(AIAgentError):
    """Raised when agent configuration is invalid."""
    pass


class ThreadNotFound(AIAgentError):
    """Raised when a conversation thread is not found."""
    pass


class PersonalityNotFound(AIAgentError):
    """Raised when a personality is not found."""
    pass