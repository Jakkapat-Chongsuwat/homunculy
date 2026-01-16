"""
Infrastructure Layer Exceptions.

CLEAN ARCHITECTURE PRINCIPLE:
Infrastructure exceptions handle technical failures (databases, APIs, external services).
These exceptions know about concrete implementations but are isolated from domain.
"""


class InfrastructureException(Exception):
    """
    Base exception for all infrastructure-level errors.

    Infrastructure exceptions represent technical failures in external systems.
    Domain layer should NOT depend on these exceptions.
    """

    def __init__(self, message: str, *args, **kwargs):
        """
        Initialize infrastructure exception.

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


# LLM Infrastructure Exceptions
class LLMException(InfrastructureException):
    """Base exception for LLM provider errors."""

    pass


class LLMConnectionException(LLMException):
    """Raised when LLM service connection fails."""

    pass


class LLMAPIException(LLMException):
    """Raised when LLM API returns an error."""

    def __init__(self, message: str, status_code: int | None = None, provider: str | None = None):
        super().__init__(message, status_code=status_code, provider=provider)


class LLMRateLimitException(LLMException):
    """Raised when LLM rate limit is exceeded."""

    pass


class LLMAuthenticationException(LLMException):
    """Raised when LLM authentication fails."""

    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message, provider=provider)


# Checkpointer/Memory Infrastructure Exceptions
class CheckpointerException(InfrastructureException):
    """Base exception for checkpointer implementation errors."""

    pass


class CheckpointerConnectionException(CheckpointerException):
    """Raised when checkpointer connection fails."""

    def __init__(self, message: str, storage_type: str | None = None):
        super().__init__(message, storage_type=storage_type)


class CheckpointerSetupException(CheckpointerException):
    """Raised when checkpointer setup/initialization fails."""

    def __init__(self, message: str, storage_type: str | None = None):
        super().__init__(message, storage_type=storage_type)


# Database Infrastructure Exceptions
class DatabaseException(InfrastructureException):
    """Base exception for database errors."""

    pass


class DatabaseConnectionException(DatabaseException):
    """Raised when database connection fails."""

    pass


class DatabaseTransactionException(DatabaseException):
    """Raised when database transaction fails."""

    pass


# External Service Exceptions
class ExternalServiceException(InfrastructureException):
    """Base exception for external service errors."""

    pass


class ServiceUnavailableException(ExternalServiceException):
    """Raised when external service is unavailable."""

    pass


class ServiceTimeoutException(ExternalServiceException):
    """Raised when external service times out."""

    pass


__all__ = [
    # Base
    "InfrastructureException",
    # LLM
    "LLMException",
    "LLMConnectionException",
    "LLMAPIException",
    "LLMRateLimitException",
    "LLMAuthenticationException",
    # Checkpointer
    "CheckpointerException",
    "CheckpointerConnectionException",
    "CheckpointerSetupException",
    # Database
    "DatabaseException",
    "DatabaseConnectionException",
    "DatabaseTransactionException",
    # External Services
    "ExternalServiceException",
    "ServiceUnavailableException",
    "ServiceTimeoutException",
]
