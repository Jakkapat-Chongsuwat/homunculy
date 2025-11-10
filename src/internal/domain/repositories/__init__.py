"""
Domain Repository Interfaces.

This package contains repository interfaces (abstract base classes) that define
the contract for data persistence operations. These are part of the domain layer
and are implemented by the infrastructure layer.
"""

from .agent_repository import AgentRepository
from .unit_of_work import UnitOfWork

__all__ = [
    "AgentRepository",
    "UnitOfWork",
]
