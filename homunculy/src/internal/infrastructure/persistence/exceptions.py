"""
Persistence Infrastructure Exceptions.

CLEAN ARCHITECTURE PRINCIPLE:
These exceptions belong in the persistence module as they represent technical failures
specific to database and storage infrastructure.
"""


class DatabaseException(Exception):
    """Base exception for database errors."""

    def __init__(self, message: str, *args, **kwargs):
        """
        Initialize database exception.

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


class DatabaseConnectionException(DatabaseException):
    """Raised when database connection fails."""

    pass


class DatabaseTransactionException(DatabaseException):
    """Raised when database transaction fails."""

    pass


__all__ = [
    "DatabaseException",
    "DatabaseConnectionException",
    "DatabaseTransactionException",
]
