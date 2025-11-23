"""
Dependency Injection Container for Infrastructure.

Provides infrastructure-level dependencies (database sessions, repositories, UoW, services).
Only contains providers that depend on concrete infrastructure implementations.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.repositories import UnitOfWork
from internal.domain.services import LLMService, TTSService
from internal.infrastructure.persistence.sqlalchemy.database import async_session_factory
from internal.infrastructure.persistence.sqlalchemy.repositories import SQLAlchemyUnitOfWork
from internal.domain.entities.agent import AgentProvider
from internal.infrastructure.services.langgraph import LangGraphAgentService
from internal.infrastructure.services.tts import ElevenLabsTTSService
from settings import settings


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.
    
    Yields:
        AsyncSession for database operations
    """
    async with async_session_factory() as session:
        yield session


async def get_uow(
    session: AsyncSession = Depends(get_session)
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
    
    Automatically injects TTS service if available, enabling TTS tools for agents.
    
    Args:
        provider: The AI provider to use (only LangGraph supported now)
        
    Returns:
        LLMService instance with persistent PostgreSQL memory and optional TTS tools
        
    Raises:
        ValueError: If provider is not supported
    """
    # Get TTS service (may be None if not configured)
    tts_service = get_tts_service()
    
    # Return new service instance (stateless - checkpointer handles persistence)
    return LangGraphAgentService(tts_service=tts_service)


def get_tts_service() -> Optional[TTSService]:
    """
    Get TTS Service dependency (Factory Pattern).
    
    Creates service instance if TTS API key is configured.
    If no API key is available, returns None (TTS tools won't be available).
    
    Returns:
        TTSService instance or None if not configured
    """
    # Try to get ElevenLabs API key from .env
    import os
    elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
    
    if elevenlabs_api_key:
        return ElevenLabsTTSService(api_key=elevenlabs_api_key)
    else:
        # TTS not configured - tools won't be available
        return None
