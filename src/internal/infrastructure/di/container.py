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
from internal.infrastructure.llm import PydanticAILLMService, LangGraphLLMService


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


def get_llm_service(provider: AgentProvider = AgentProvider.PYDANTIC_AI) -> LLMService:
    """
    Get LLM Service dependency.
    
    Factory function that returns the appropriate LLM service based on provider.
    
    Args:
        provider: The AI provider to use (defaults to PydanticAI)
        
    Returns:
        LLMService instance for AI interactions
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider == AgentProvider.LANGRAPH:
        return LangGraphLLMService()
    elif provider in (AgentProvider.PYDANTIC_AI, AgentProvider.OPENAI):
        return PydanticAILLMService()
    else:
        raise ValueError(f"Unsupported agent provider: {provider}")
