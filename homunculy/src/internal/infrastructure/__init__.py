"""
Infrastructure Layer.

This layer contains all external concerns and implementations:
- Persistence (databases, file storage)
- External services (APIs, message queues)
- Dependency injection
- Framework integrations
"""

from .persistence import (
    SQLAlchemyAgentRepository,
    SQLAlchemyUnitOfWork,
    init_db,
    close_db,
)
from .di import get_session, get_uow

__all__ = [
    # Persistence - SQLAlchemy
    "SQLAlchemyAgentRepository",
    "SQLAlchemyUnitOfWork",
    "init_db",
    "close_db",
    # Dependency Injection
    "get_session",
    "get_uow",
]
