"""
HTTP Adapters (Controllers).

This package contains HTTP request handlers that adapt external HTTP requests
to use case calls. This is the interface adapter layer in Clean Architecture.
"""

from . import agent_handler

__all__ = [
    "agent_handler",
]
