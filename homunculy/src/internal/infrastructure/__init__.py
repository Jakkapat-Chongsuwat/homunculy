"""
Infrastructure Layer.

This layer contains all external concerns and implementations:
- Service implementations (LLM, TTS)
- Persistence (databases, repositories)
- Dependency injection container
- Framework integrations (LangGraph)
"""

from .container import (
    get_llm_service,
    get_session,
    get_tts_service,
    get_uow,
)
from .persistence import (
    SQLAlchemyAgentRepository,
    SQLAlchemyUnitOfWork,
    close_db,
    init_db,
)
from .services import (
    ElevenLabsTTSService,
    LangGraphAgentService,
)

__all__ = [
    # Persistence - SQLAlchemy
    "SQLAlchemyAgentRepository",
    "SQLAlchemyUnitOfWork",
    "init_db",
    "close_db",
    # Services
    "LangGraphAgentService",
    "ElevenLabsTTSService",
    # Dependency Injection
    "get_session",
    "get_uow",
    "get_llm_service",
    "get_tts_service",
]
