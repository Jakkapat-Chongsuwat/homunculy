"""
Dependency Injection Container.

Provides centralized service instantiation and dependency injection.
"""

from .service_providers import (
    get_session,
    get_uow,
    get_llm_service,
    get_tts_service,
)

__all__ = [
    "get_session",
    "get_uow",
    "get_llm_service",
    "get_tts_service",
]
