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
from internal.infrastructure.persistence.sqlalchemy import (
    async_session_factory,
    SQLAlchemyUnitOfWork,
)
from internal.domain.entities.agent import AgentProvider
from internal.infrastructure.agents import LangGraphAgentService
from internal.infrastructure.tts import ElevenLabsTTSService
from settings import settings

# Singleton instances to persist across requests
_llm_service_instance = None
_tts_service_instance = None

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
    Get LLM Service dependency (Singleton).
    
    CRITICAL: Returns a singleton instance to ensure the MemorySaver checkpointer
    persists across HTTP requests within the same container lifecycle.
    
    Automatically injects TTS service if available, enabling TTS tools for agents.
    
    Args:
        provider: The AI provider to use (only LangGraph supported now)
        
    Returns:
        LLMService singleton instance with persistent memory and optional TTS tools
        
    Raises:
        ValueError: If provider is not supported
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        # Get TTS service (may be None if not configured)
        tts_service = get_tts_service()
        
        # Initialize singleton agent service with optional TTS tools
        _llm_service_instance = LangGraphAgentService(tts_service=tts_service)
    
    return _llm_service_instance


def get_tts_service() -> Optional[TTSService]:
    """
    Get TTS Service dependency (Singleton).
    
    Returns a singleton instance if TTS API key is configured.
    If no API key is available, returns None (TTS tools won't be available).
    
    Returns:
        TTSService singleton instance or None if not configured
    """
    global _tts_service_instance
    
    if _tts_service_instance is None:
        # Try to get ElevenLabs API key from .env
        import os
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        if elevenlabs_api_key:
            _tts_service_instance = ElevenLabsTTSService(api_key=elevenlabs_api_key)
        else:
            # TTS not configured - tools won't be available
            _tts_service_instance = None
    
    return _tts_service_instance
