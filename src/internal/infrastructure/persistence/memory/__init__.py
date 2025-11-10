"""
In-Memory Persistence Layer.

This package contains in-memory implementations for testing and development.
"""

from .agent_repository import MemoryAgentRepository

__all__ = [
    "MemoryAgentRepository",
]
