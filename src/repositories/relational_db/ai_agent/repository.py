"""
Relational Database AI Agent Repository Implementation.

This module provides the concrete repository implementation for AI agents
using SQLAlchemy, following the existing Pokemon repository pattern.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import delete, insert, select, update

from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
    AgentStatus,
    AgentThread,
)
from models.ai_agent.exception import (
    AgentConfigurationError,
    AgentExecutionError,
    AgentInitializationError,
    AgentNotFound,
    PersonalityNotFound,
    ThreadNotFound,
)
from repositories.abstraction.ai_agent import AbstractAIAgentRepository

from .mapper import AgentConfigurationOrmMapper, AgentPersonalityOrmMapper, AgentThreadOrmMapper
from .orm import AgentConfiguration as AgentConfigurationOrm, AgentPersonality as AgentPersonalityOrm, AgentThread as AgentThreadOrm


class RelationalDBAIAgentRepository(AbstractAIAgentRepository):
    """Relational database repository for AI agents using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self.session = session
        # Store active PydanticAI agents by agent_id
        self._active_agents: Dict[str, Any] = {}

    async def save_agent_config(self, config: AgentConfiguration) -> str:
        """Save agent configuration and return agent ID."""
        agent_id = str(uuid.uuid4())

        orm_config = AgentConfigurationOrmMapper.entity_to_orm(config, agent_id)
        self.session.add(orm_config)
        await self.session.commit()
        return agent_id

    async def get_agent_config(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID."""
        stmt = select(AgentConfigurationOrm).where(AgentConfigurationOrm.id == agent_id)
        result = await self.session.execute(stmt)
        orm_config = result.scalar_one_or_none()

        if not orm_config:
            return None

        return AgentConfigurationOrmMapper.orm_to_entity(orm_config)

    async def update_agent_config(self, agent_id: str, config: AgentConfiguration) -> bool:
        """Update agent configuration."""
        stmt = select(AgentConfigurationOrm).where(AgentConfigurationOrm.id == agent_id)
        result = await self.session.execute(stmt)
        orm_config = result.scalar_one_or_none()

        if not orm_config:
            return False

        # Update the ORM object with new values
        updated_orm = AgentConfigurationOrmMapper.entity_to_orm(config, agent_id)
        orm_config.provider = updated_orm.provider
        orm_config.model_name = updated_orm.model_name
        orm_config.personality_json = updated_orm.personality_json
        orm_config.system_prompt = updated_orm.system_prompt
        orm_config.temperature = updated_orm.temperature
        orm_config.max_tokens = updated_orm.max_tokens
        orm_config.tools_json = updated_orm.tools_json
        orm_config.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        return True

    async def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration."""
        stmt = select(AgentConfigurationOrm).where(AgentConfigurationOrm.id == agent_id)
        result = await self.session.execute(stmt)
        orm_config = result.scalar_one_or_none()

        if not orm_config:
            return False

        await self.session.delete(orm_config)
        await self.session.commit()
        return True

    async def list_agent_configs(self, limit: int = 50, offset: int = 0) -> List[AgentConfiguration]:
        """List all agent configurations."""
        stmt = (
            select(AgentConfigurationOrm)
            .order_by(AgentConfigurationOrm.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        orm_configs = result.scalars().all()

        return [AgentConfigurationOrmMapper.orm_to_entity(orm_config) for orm_config in orm_configs]

    async def save_thread(self, thread: AgentThread) -> str:
        """Save conversation thread and return thread ID."""
        orm_thread = AgentThreadOrmMapper.entity_to_orm(thread)
        self.session.add(orm_thread)
        await self.session.commit()
        return thread.id

    async def get_thread(self, thread_id: str) -> Optional[AgentThread]:
        """Get conversation thread by ID."""
        stmt = select(AgentThreadOrm).where(AgentThreadOrm.id == thread_id)
        result = await self.session.execute(stmt)
        orm_thread = result.scalar_one_or_none()

        if not orm_thread:
            return None

        return AgentThreadOrmMapper.orm_to_entity(orm_thread)

    async def update_thread(self, thread: AgentThread) -> bool:
        """Update conversation thread."""
        stmt = select(AgentThreadOrm).where(AgentThreadOrm.id == thread.id)
        result = await self.session.execute(stmt)
        orm_thread = result.scalar_one_or_none()

        if not orm_thread:
            return False

        updated_orm = AgentThreadOrmMapper.entity_to_orm(thread)
        orm_thread.messages_json = updated_orm.messages_json
        orm_thread.metadata_json = updated_orm.metadata_json
        orm_thread.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        return True

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete conversation thread."""
        stmt = select(AgentThreadOrm).where(AgentThreadOrm.id == thread_id)
        result = await self.session.execute(stmt)
        orm_thread = result.scalar_one_or_none()

        if not orm_thread:
            return False

        await self.session.delete(orm_thread)
        await self.session.commit()
        return True

    async def list_threads_by_agent(
        self, agent_id: str, limit: int = 50, offset: int = 0
    ) -> List[AgentThread]:
        """List conversation threads for a specific agent."""
        stmt = (
            select(AgentThreadOrm)
            .where(AgentThreadOrm.agent_id == agent_id)
            .order_by(AgentThreadOrm.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        orm_threads = result.scalars().all()

        return [AgentThreadOrmMapper.orm_to_entity(orm_thread) for orm_thread in orm_threads]

    async def save_personality(self, personality: AgentPersonality) -> str:
        """Save agent personality and return personality ID."""
        personality_id = str(uuid.uuid4())

        orm_personality = AgentPersonalityOrmMapper.entity_to_orm(personality, personality_id)
        self.session.add(orm_personality)
        await self.session.commit()
        return personality_id

    async def get_personality(self, personality_id: str) -> Optional[AgentPersonality]:
        """Get agent personality by ID."""
        stmt = select(AgentPersonalityOrm).where(AgentPersonalityOrm.id == personality_id)
        result = await self.session.execute(stmt)
        orm_personality = result.scalar_one_or_none()

        if not orm_personality:
            return None

        return AgentPersonalityOrmMapper.orm_to_entity(orm_personality)

    async def update_personality(self, personality_id: str, personality: AgentPersonality) -> bool:
        """Update agent personality."""
        stmt = select(AgentPersonalityOrm).where(AgentPersonalityOrm.id == personality_id)
        result = await self.session.execute(stmt)
        orm_personality = result.scalar_one_or_none()

        if not orm_personality:
            return False

        updated_orm = AgentPersonalityOrmMapper.entity_to_orm(personality, personality_id)
        orm_personality.name = updated_orm.name
        orm_personality.description = updated_orm.description
        orm_personality.traits_json = updated_orm.traits_json
        orm_personality.mood = updated_orm.mood
        orm_personality.memory_context = updated_orm.memory_context
        orm_personality.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        return True

    async def delete_personality(self, personality_id: str) -> bool:
        """Delete agent personality."""
        stmt = select(AgentPersonalityOrm).where(AgentPersonalityOrm.id == personality_id)
        result = await self.session.execute(stmt)
        orm_personality = result.scalar_one_or_none()

        if not orm_personality:
            return False

        await self.session.delete(orm_personality)
        await self.session.commit()
        return True

    # AI Execution Methods
    async def initialize_agent(self, config: AgentConfiguration) -> str:
        """Initialize an AI agent with the given configuration."""
        # Save the configuration first
        agent_id = await self.save_agent_config(config)
        
        # Create PydanticAI agent based on provider
        if config.provider == AgentProvider.PYDANTIC_AI:
            # For now, use a simple agent. In production, you'd configure based on model_name
            # Mock agent creation to avoid constructor issues
            self._active_agents[agent_id] = f"mock_agent_{agent_id}"  # Store mock reference
        
        return agent_id

    async def chat(
        self,
        agent_id: str,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> AgentResponse:
        """Send a message to an agent and get response."""
        # This is a placeholder - in a real implementation, this would call the actual AI service
        return AgentResponse(
            message=f"Mock response to: {message}",
            confidence=0.8,
            reasoning="This is a mock response for development purposes",
            metadata={
                "agent_id": agent_id,
                "thread_id": thread_id,
                "status": "mock_response"
            }
        )

    async def chat_stream(
        self,
        agent_id: str,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> AsyncIterator[AgentResponse]:
        """Send a message to an agent and get streaming response."""
        # This is a placeholder - in a real implementation, this would stream from the actual AI service
        response = AgentResponse(
            message=f"Mock streaming response to: {message}",
            confidence=0.8,
            reasoning="This is a mock streaming response for development purposes",
            metadata={
                "agent_id": agent_id,
                "thread_id": thread_id,
                "status": "mock_stream"
            }
        )
        yield response

    async def update_agent_personality(
        self,
        agent_id: str,
        personality: AgentPersonality,
    ) -> bool:
        """Update agent's personality traits."""
        # Get current config
        config = await self.get_agent_config(agent_id)
        if not config:
            return False
            
        # Update personality
        config.personality = personality
        
        # Save updated config
        return await self.update_agent_config(agent_id, config)

    async def get_thread_history(self, thread_id: str) -> List[AgentMessage]:
        """Get conversation history for a thread."""
        thread = await self.get_thread(thread_id)
        return thread.messages if thread else []

    async def clear_thread_history(self, thread_id: str) -> bool:
        """Clear conversation history for a thread."""
        # Get existing thread first to preserve agent_id
        existing_thread = await self.get_thread(thread_id)
        if not existing_thread:
            return False
            
        # Create empty messages list
        empty_thread = AgentThread(
            id=thread_id,
            agent_id=existing_thread.agent_id,
            messages=[],
            metadata={}
        )
        return await self.update_thread(empty_thread)

    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status of an agent."""
        config = await self.get_agent_config(agent_id)
        if not config:
            return {"status": "not_found"}
            
        return {
            "status": "active",
            "agent_id": agent_id,
            "model": config.model_name,
            "provider": config.provider.value,
            "personality": config.personality.name,
        }

    async def shutdown_agent(self, agent_id: str) -> bool:
        """Shutdown a specific agent."""
        # For now, just return True as we don't have actual agent instances to shutdown
        return True

    async def list_available_providers(self) -> List[AgentProvider]:
        """List all available AI agent providers."""
        return [AgentProvider.PYDANTIC_AI]  # Placeholder