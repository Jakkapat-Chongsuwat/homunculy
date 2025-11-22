"""
Dependency Injection Container for Infrastructure.

Provides infrastructure-level dependencies (database sessions, repositories, UoW, services).
Only contains providers that depend on concrete infrastructure implementations.
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from internal.domain.repositories import UnitOfWork
from internal.domain.services import LLMService
from internal.infrastructure.persistence.sqlalchemy import (
    async_session_factory,
    SQLAlchemyUnitOfWork,
)
from internal.domain.entities.agent import AgentProvider
from internal.infrastructure.agents import LangGraphAgentService

# Singleton instance to persist memory across requests
_llm_service_instance = None

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
    
    Args:
        provider: The AI provider to use (only LangGraph supported now)
        
    Returns:
        LLMService singleton instance with persistent memory
        
    Raises:
        ValueError: If provider is not supported
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        # Initialize singleton agent service
        _llm_service_instance = LangGraphAgentService()
    
    return _llm_service_instance
