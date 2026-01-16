"""
Dependency Injection Container for Infrastructure.

Provides infrastructure-level dependencies (database sessions, repositories, UoW, services).
Only contains providers that depend on concrete infrastructure implementations.
"""

import os
from typing import AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.entities.agent import AgentProvider
from internal.domain.repositories import UnitOfWork
from internal.domain.services import LLMService, RAGService, TTSService
from internal.infrastructure.container.di_container import get_container
from internal.infrastructure.persistence.sqlalchemy.database import (
    async_session_factory,
)
from internal.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyUnitOfWork,
)
from internal.infrastructure.services.langgraph.checkpointer import create_checkpointer_manager
from internal.infrastructure.services.langgraph.graph import GraphManager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Yields:
        AsyncSession for database operations
    """
    async with async_session_factory() as session:
        yield session


async def get_uow(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Get Unit of Work dependency.

    Args:
        session: Database session from dependency

    Yields:
        UnitOfWork instance for managing transactions
    """
    async with SQLAlchemyUnitOfWork(session) as uow:
        yield uow


def get_llm_service(provider: AgentProvider = AgentProvider.LANGRAPH) -> LLMService:
    """
    Get LLM Service dependency (Factory Pattern).

    Creates service instance with AsyncPostgresSaver checkpointer that persists
    conversation state across requests. Each request gets the same checkpointer
    instance via shared database connection.

    Automatically injects TTS and RAG services if available.

    Args:
        provider: The AI provider to use (only LangGraph supported now)

    Returns:
        LLMService instance with persistent PostgreSQL memory and optional tools

    Raises:
        ValueError: If provider is not supported
    """
    return get_container().llm_service()


def get_tts_service() -> Optional[TTSService]:
    """
    Get TTS Service dependency (Factory Pattern).

    Creates service instance if TTS API key is configured.
    If no API key is available, returns None (TTS tools won't be available).

    Returns:
        TTSService instance or None if not configured
    """
    return get_container().tts_service()


def get_rag_service() -> Optional[RAGService]:
    """
    Get RAG Service dependency (Factory Pattern).

    Creates HTTP RAG service if RAG_SERVICE_URL is configured.
    If not configured, returns None (RAG tools won't be available).

    Returns:
        RAGService instance or None if not configured
    """
    return get_container().rag_service()


def get_graph_manager() -> GraphManager:
    """
    Get Graph Manager dependency.

    Creates a GraphManager with configured services and checkpointer.
    Used for Pipecat integration to access compiled graphs.
    """
    api_key = os.getenv("LLM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    # Use default checkpointer (Postgres if DB available, else Memory)
    checkpointer_mgr = create_checkpointer_manager(None)

    return GraphManager(
        api_key=api_key,
        checkpointer=checkpointer_mgr.get_checkpointer(),
        tts_service=get_tts_service(),
        rag_service=get_rag_service(),
    )
