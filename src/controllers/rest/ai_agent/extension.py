"""
AI Agent REST API Extensions.

This module provides utility functions to integrate FastAPI exception handlers with the application's
domain-specific exceptions for AI agent operations.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from models.ai_agent.exception import (
    AIAgentError,
    AgentNotFound,
    PersonalityNotFound,
    ThreadNotFound,
)


def add_ai_agent_exception_handlers(app: FastAPI):
    """Add exception handlers for AI agent-related errors."""
    @app.exception_handler(AIAgentError)
    async def handle_general_agent_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(content={'error': f'{type(exc).__name__}: {exc}'}, status_code=400)

    @app.exception_handler(AgentNotFound)
    @app.exception_handler(PersonalityNotFound)
    @app.exception_handler(ThreadNotFound)
    async def handle_agent_not_found_error(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(content={'error': f'{type(exc).__name__}: {exc}'}, status_code=404)