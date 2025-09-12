"""
AI Agent REST API Routes.

This module provides REST API endpoints for AI agent operations,
following the Clean Architecture pattern established in the Pokemon system.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from injector import inject

from di.dependency_injection import injector
from di.unit_of_work import AbstractUnitOfWork
from models.ai_agent import AgentConfiguration, AgentPersonality, AgentProvider, AgentResponse
from usecases import ai_agent_crud

router = APIRouter()


def get_unit_of_work() -> AbstractUnitOfWork:
    """Dependency injection for Unit of Work."""
    return injector.get(AbstractUnitOfWork)


@router.post("/agents", response_model=Dict[str, str])
async def create_agent(
    config: AgentConfiguration,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """Create a new AI agent."""
    try:
        agent_id = await ai_agent_crud.initialize_ai_agent(uow, config)
        return {"agent_id": agent_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.post("/agents/{agent_id}/chat", response_model=AgentResponse)
async def chat_with_agent(
    agent_id: str,
    message: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict] = None,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """Send a message to an AI agent."""
    try:
        return await ai_agent_crud.chat_with_agent(uow, agent_id, message, thread_id, context)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chat with agent: {str(e)}"
        )


@router.put("/agents/{agent_id}/personality")
async def update_agent_personality(
    agent_id: str,
    personality: AgentPersonality,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """Update an agent's personality."""
    try:
        success = await ai_agent_crud.update_agent_personality(uow, agent_id, personality)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update personality: {str(e)}"
        )


@router.get("/agents/{agent_id}/config", response_model=AgentConfiguration)
async def get_agent_config(
    agent_id: str,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """Get agent configuration."""
    try:
        config = await ai_agent_crud.get_agent_configuration(uow, agent_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent config: {str(e)}"
        )


@router.get("/agents/{agent_id}/status")
async def get_agent_status(
    agent_id: str,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """Get agent status."""
    try:
        return await ai_agent_crud.get_agent_status(uow, agent_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/providers", response_model=List[AgentProvider])
async def list_providers(
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """List available AI providers."""
    try:
        return await ai_agent_crud.list_available_providers(uow)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.delete("/agents/{agent_id}")
async def shutdown_agent(
    agent_id: str,
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
):
    """Shutdown an AI agent."""
    try:
        success = await ai_agent_crud.shutdown_agent(uow, agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        return {"status": "shutdown"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to shutdown agent: {str(e)}"
        )