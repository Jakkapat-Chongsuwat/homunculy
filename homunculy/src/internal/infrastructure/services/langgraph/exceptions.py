"""
LangGraph Service Exceptions.

CLEAN ARCHITECTURE PRINCIPLE:
These exceptions belong in the langgraph service module as they represent technical failures
specific to LangGraph agent infrastructure (checkpointers, memory, LLM auth, etc.).
"""


class LLMAuthenticationException(Exception):
    """Raised when LLM API authentication fails."""
    
    def __init__(self, message: str, provider: str | None = None):
        """
        Initialize LLM authentication exception.
        
        Args:
            message: Human-readable error message
            provider: LLM provider name (e.g., 'openai')
        """
        self.message = message
        self.provider = provider
        super().__init__(message)
    
    def __str__(self) -> str:
        """String representation of the exception."""
        if self.provider:
            return f"{self.message} (provider={self.provider})"
        return self.message


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


class GraphExecutionException(Exception):
    """Raised when LangGraph execution fails."""
    
    def __init__(self, message: str, thread_id: str | None = None, **kwargs):
        self.message = message
        self.thread_id = thread_id
        self.context = kwargs
        super().__init__(message)
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.thread_id:
            parts.append(f"thread_id={self.thread_id}")
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(context_str)
        return f"{parts[0]} ({', '.join(parts[1:])})" if len(parts) > 1 else parts[0]


class GraphStateException(Exception):
    """Raised when graph state retrieval/manipulation fails."""
    
    def __init__(self, message: str, thread_id: str | None = None):
        self.message = message
        self.thread_id = thread_id
        super().__init__(message)


__all__ = [
    "LLMAuthenticationException",
    "CheckpointerException",
    "CheckpointerConnectionException",
    "CheckpointerSetupException",
    "GraphExecutionException",
    "GraphStateException",
]
