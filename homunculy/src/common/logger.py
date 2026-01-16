"""
Structured logging configuration using structlog.

Provides production-ready JSON logging with request correlation
and context binding for observability.

The Logger protocol provides duck-typing interface for swappable logging backends.
"""

import logging
import sys
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    import structlog
    from structlog.typing import FilteringBoundLogger

try:
    import structlog
    from structlog.typing import FilteringBoundLogger

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False
    structlog = None
    FilteringBoundLogger = Any

from settings.logging import LogFormat, logging_settings


@runtime_checkable
class Logger(Protocol):
    """
    Logger protocol for duck-typing compatibility.

    Allows swapping between structlog, standard logging, or custom implementations
    without changing client code. Follows Dependency Inversion Principle.

    Example:
        logger: Logger = get_logger(__name__)
        logger.info("message", key="value")
    """

    def debug(self, event: str, **kwargs: Any) -> Any:
        """Log debug message with context."""
        ...

    def info(self, event: str, **kwargs: Any) -> Any:
        """Log info message with context."""
        ...

    def warning(self, event: str, **kwargs: Any) -> Any:
        """Log warning message with context."""
        ...

    def error(self, event: str, **kwargs: Any) -> Any:
        """Log error message with context."""
        ...

    def critical(self, event: str, **kwargs: Any) -> Any:
        """Log critical message with context."""
        ...

    def exception(self, event: str, **kwargs: Any) -> Any:
        """Log exception with traceback."""
        ...


def configure_logging() -> None:
    """
    Configure application logging with structlog.

    Uses JSON format in production for log aggregation tools.
    Uses colored console output in development for readability.
    """
    if not HAS_STRUCTLOG or logging_settings.log_format == LogFormat.TEXT:
        _configure_standard_logging()
        return

    _configure_structlog()


def _configure_standard_logging() -> None:
    """Configure standard Python logging (fallback)."""
    logging.basicConfig(
        level=logging_settings.level,
        format=logging_settings.format,
        datefmt=logging_settings.date_format,
        stream=sys.stdout,
    )
    logging.info("Standard logging configured", extra={"format": "text"})


def _configure_structlog() -> None:
    """Configure structlog for structured JSON logging."""
    if not HAS_STRUCTLOG or structlog is None:
        return

    # Determine if we're in development mode
    is_dev = logging_settings.level == "DEBUG"

    # Build processor chain
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
    ]

    # Add renderer based on environment
    if is_dev:
        # Colored console output for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging_settings.level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging_settings.level,
    )

    # Get logger to confirm configuration
    logger = structlog.get_logger()
    logger.info(
        "Structlog configured",
        format="json" if not is_dev else "console",
        level=logging_settings.level,
    )


class StandardLoggerAdapter:
    """
    Adapter to make stdlib logging.Logger compatible with Logger protocol.

    Converts structlog-style keyword arguments to stdlib extra dict.
    Enables consistent logging interface across different backends.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(event, extra=kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(event, extra=kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(event, extra=kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        exc_info = kwargs.pop("exc_info", False)
        self._logger.error(event, extra=kwargs, exc_info=exc_info)

    def critical(self, event: str, **kwargs: Any) -> None:
        self._logger.critical(event, extra=kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception(event, extra=kwargs)


def get_logger(name: Optional[str] = None) -> Logger:
    """
    Get a structured logger instance.

    Returns a logger that conforms to the Logger protocol, enabling
    dependency injection and testability. The actual implementation
    (structlog or stdlib) is determined by configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger implementation (structlog or standard logging)

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id=123, ip="127.0.0.1")
    """
    if HAS_STRUCTLOG and structlog is not None and logging_settings.log_format == LogFormat.JSON:
        return structlog.get_logger(name)
    else:
        stdlib_logger = logging.getLogger(name or __name__)
        return StandardLoggerAdapter(stdlib_logger)
