"""
Dependency Injection for Infrastructure.

This package contains DI container for infrastructure-level dependencies only.
"""

from .container import get_session, get_uow

__all__ = [
    "get_session",
    "get_uow",
]
