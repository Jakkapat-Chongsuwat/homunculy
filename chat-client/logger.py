"""
Logging Utilities using structlog.
"""

import os
import sys
from typing import Any

import structlog


def _configure_structlog() -> None:
    """Configure structlog with appropriate processors."""
    is_debug = os.environ.get("DEBUG", "0") == "1"

    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(colors=True),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            min_level=0 if is_debug else 30  # DEBUG=0, WARN=30
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


_configure_structlog()
log: structlog.stdlib.BoundLogger = structlog.get_logger()
