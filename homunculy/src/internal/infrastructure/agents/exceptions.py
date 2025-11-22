"""
Agent Infrastructure Exceptions.

CLEAN ARCHITECTURE PRINCIPLE:
These exceptions belong in the agents module as they represent technical failures
specific to agent infrastructure (checkpointers, memory, etc.).
"""


class CheckpointerException(Exception):
    """Base exception for checkpointer implementation errors."""
    
    def __init__(self, message: str, *args, **kwargs):
        """
        Initialize checkpointer exception.
        
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


class CheckpointerConnectionException(CheckpointerException):
    """Raised when checkpointer connection fails."""
    
    def __init__(self, message: str, storage_type: str | None = None):
        super().__init__(message, storage_type=storage_type)


class CheckpointerSetupException(CheckpointerException):
    """Raised when checkpointer setup/initialization fails."""
    
    def __init__(self, message: str, storage_type: str | None = None):
        super().__init__(message, storage_type=storage_type)


__all__ = [
    "CheckpointerException",
    "CheckpointerConnectionException",
    "CheckpointerSetupException",
]
