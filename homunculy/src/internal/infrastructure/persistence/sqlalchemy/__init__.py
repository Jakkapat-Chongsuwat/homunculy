"""
SQLAlchemy Persistence Layer.

This package contains SQLAlchemy-specific implementations for data persistence,
including ORM models, repositories, sessions, and Unit of Work.
"""

from .database.session_manager import (
    Base,
    async_session_factory,
    close_db,
    engine,
    get_db_session,
    init_db,
)
from .models import AgentModel
from .repositories import (
    SQLAlchemyAgentRepository,
    SQLAlchemyUnitOfWork,
)

__all__ = [
    # Session & Engine
    "engine",
    "async_session_factory",
    "get_db_session",
    "init_db",
    "close_db",
    "Base",
    # Models
    "AgentModel",
    # Repository
    "SQLAlchemyAgentRepository",
    # Unit of Work
    "SQLAlchemyUnitOfWork",
]
