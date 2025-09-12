"""
Extensions for Controller Layer.

This module provides utility functions to integrate FastAPI exception handlers with the application's
domain-specific exceptions. It ensures that custom errors in the domain layer are transformed into appropriate
HTTP responses when they propagate to the REST layer.

Note:
    For simpler requirements, use extension.py. For more complex needs, consider extensions/$package.py for better clarity and scalability.
"""

from fastapi import FastAPI

from .ai_agent.extension import add_ai_agent_exception_handlers
from .pokemon.extension import add_pokemon_exception_handlers


def add_exception_handlers(app: FastAPI):
    """Add all exception handlers for the application."""
    add_pokemon_exception_handlers(app)
    add_ai_agent_exception_handlers(app)
