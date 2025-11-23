"""
Infrastructure Layer.

This layer contains all external concerns and implementations:
- Service implementations (LLM, TTS)
- Persistence (databases, repositories)
- Dependency injection container
- Framework integrations (LangGraph)
"""

from .persistence import (
    SQLAlchemyAgentRepository,
    SQLAlchemyUnitOfWork,
    init_db,
    close_db,
)
from .services import (
    LangGraphAgentService,
    ElevenLabsTTSService,
)
from .container import (
    get_session,
    get_uow,
    get_llm_service,
    get_tts_service,
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
