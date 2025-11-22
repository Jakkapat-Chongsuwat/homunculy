"""
LLM Infrastructure Exceptions.

CLEAN ARCHITECTURE PRINCIPLE:
These exceptions belong in the LLM module as they represent technical failures
specific to LLM providers (OpenAI, Anthropic, etc.).
"""


class LLMException(Exception):
    """Base exception for LLM provider errors."""
    
    def __init__(self, message: str, *args, **kwargs):
        """
        Initialize LLM exception.
        
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


class LLMConnectionException(LLMException):
    """Raised when LLM service connection fails."""
    pass


class LLMAPIException(LLMException):
    """Raised when LLM API returns an error."""
    
    def __init__(self, message: str, status_code: int | None = None, provider: str | None = None):
        super().__init__(
            message,
            status_code=status_code,
            provider=provider
        )


class LLMRateLimitException(LLMException):
    """Raised when LLM rate limit is exceeded."""
    pass


class LLMAuthenticationException(LLMException):
    """Raised when LLM authentication fails."""
    
    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message, provider=provider)


__all__ = [
    "LLMException",
    "LLMConnectionException",
    "LLMAPIException",
    "LLMRateLimitException",
    "LLMAuthenticationException",
]
