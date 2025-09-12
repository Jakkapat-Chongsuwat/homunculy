"""
Relational Database AI Agent Repository Implementation.

This module provides the concrete repository implementation for AI agents
using SQLAlchemy, following the existing Pokemon repository pattern.
"""

import json
import uuid
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai import Agent
from sqlalchemy.orm import declarative_base

from models.ai_agent import (
    AgentConfiguration,
    AgentMessage,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
    AgentStatus,
    AgentThread,
)
from repositories.abstraction.ai_agent import AbstractAIAgentRepository

# Create base class for our models
Base = declarative_base()


class AgentConfigurationEntity(Base):
    """SQLAlchemy model for agent configurations."""
    
    __tablename__ = "ai_agent_configurations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    personality_json = Column(Text, nullable=False)  # JSON serialized personality
    system_prompt = Column(Text, default="")
    temperature = Column(String, default="0.7")  # Store as string to avoid float precision issues
    max_tokens = Column(Integer, default=2000)
    tools_json = Column(Text, default="[]")  # JSON serialized list of tools
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentThreadEntity(Base):
    """SQLAlchemy model for agent threads."""
    
    __tablename__ = "ai_agent_threads"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False)
    messages_json = Column(Text, default="[]")  # JSON serialized messages
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_json = Column(Text, default="{}")  # JSON serialized metadata


class AgentPersonalityEntity(Base):
    """SQLAlchemy model for agent personalities."""
    
    __tablename__ = "ai_agent_personalities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    traits_json = Column(Text, default="{}")  # JSON serialized traits
    mood = Column(String, default="neutral")
    memory_context = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RelationalDBAIAgentRepository(AbstractAIAgentRepository):
    """Relational database repository for AI agents using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        self.session = session
        # Store active PydanticAI agents by agent_id
        self._active_agents: Dict[str, Agent] = {}

    async def save_agent_config(self, config: AgentConfiguration) -> str:
        """Save agent configuration and return agent ID."""
        agent_id = str(uuid.uuid4())
        
        entity = AgentConfigurationEntity(
            id=agent_id,
            provider=config.provider.value,
            model_name=config.model_name,
            personality_json=config.personality.model_dump_json(),
            system_prompt=config.system_prompt,
            temperature=str(config.temperature),
            max_tokens=config.max_tokens,
            tools_json=json.dumps(config.tools),
        )
        
        self.session.add(entity)
        await self.session.commit()
        return agent_id

    async def get_agent_config(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID."""
        stmt = select(AgentConfigurationEntity).where(AgentConfigurationEntity.id == agent_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return None
        
        personality_data = json.loads(entity.personality_json)
        personality = AgentPersonality(**personality_data)
        
        return AgentConfiguration(
            provider=AgentProvider(entity.provider),
            model_name=entity.model_name,
            personality=personality,
            system_prompt=entity.system_prompt,
            temperature=float(entity.temperature),
            max_tokens=entity.max_tokens,
            tools=json.loads(entity.tools_json),
        )

    async def update_agent_config(self, agent_id: str, config: AgentConfiguration) -> bool:
        """Update agent configuration."""
        stmt = select(AgentConfigurationEntity).where(AgentConfigurationEntity.id == agent_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        entity.provider = config.provider.value
        entity.model_name = config.model_name
        entity.personality_json = config.personality.model_dump_json()
        entity.system_prompt = config.system_prompt
        entity.temperature = str(config.temperature)
        entity.max_tokens = config.max_tokens
        entity.tools_json = json.dumps(config.tools)
        entity.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return True

    async def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration."""
        stmt = select(AgentConfigurationEntity).where(AgentConfigurationEntity.id == agent_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        await self.session.delete(entity)
        await self.session.commit()
        return True

    async def list_agent_configs(self, limit: int = 50, offset: int = 0) -> List[AgentConfiguration]:
        """List all agent configurations."""
        stmt = (
            select(AgentConfigurationEntity)
            .order_by(AgentConfigurationEntity.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        
        configs = []
        for entity in entities:
            personality_data = json.loads(entity.personality_json)
            personality = AgentPersonality(**personality_data)
            
            config = AgentConfiguration(
                provider=AgentProvider(entity.provider),
                model_name=entity.model_name,
                personality=personality,
                system_prompt=entity.system_prompt,
                temperature=float(entity.temperature),
                max_tokens=entity.max_tokens,
                tools=json.loads(entity.tools_json),
            )
            configs.append(config)
        
        return configs

    async def save_thread(self, thread: AgentThread) -> str:
        """Save conversation thread and return thread ID."""
        # Convert messages to JSON
        messages_data = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata or {},
            }
            for msg in thread.messages
        ]
        
        entity = AgentThreadEntity(
            id=thread.id,
            agent_id=thread.agent_id,
            messages_json=json.dumps(messages_data),
            metadata_json=json.dumps(thread.metadata),
        )
        
        self.session.add(entity)
        await self.session.commit()
        return thread.id

    async def get_thread(self, thread_id: str) -> Optional[AgentThread]:
        """Get conversation thread by ID."""
        stmt = select(AgentThreadEntity).where(AgentThreadEntity.id == thread_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return None
        
        # Parse messages from JSON
        messages_data = json.loads(entity.messages_json)
        messages = [
            AgentMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata"),
            )
            for msg_data in messages_data
        ]
        
        return AgentThread(
            id=entity.id,
            agent_id=entity.agent_id,
            messages=messages,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            metadata=json.loads(entity.metadata_json),
        )

    async def update_thread(self, thread: AgentThread) -> bool:
        """Update conversation thread."""
        stmt = select(AgentThreadEntity).where(AgentThreadEntity.id == thread.id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        # Convert messages to JSON
        messages_data = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata or {},
            }
            for msg in thread.messages
        ]
        
        entity.messages_json = json.dumps(messages_data)
        entity.metadata_json = json.dumps(thread.metadata)
        entity.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return True

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete conversation thread."""
        stmt = select(AgentThreadEntity).where(AgentThreadEntity.id == thread_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        await self.session.delete(entity)
        await self.session.commit()
        return True

    async def list_threads_by_agent(
        self, agent_id: str, limit: int = 50, offset: int = 0
    ) -> List[AgentThread]:
        """List conversation threads for a specific agent."""
        stmt = (
            select(AgentThreadEntity)
            .where(AgentThreadEntity.agent_id == agent_id)
            .order_by(AgentThreadEntity.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        entities = result.scalars().all()
        
        threads = []
        for entity in entities:
            # Parse messages from JSON
            messages_data = json.loads(entity.messages_json)
            messages = [
                AgentMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data.get("metadata"),
                )
                for msg_data in messages_data
            ]
            
            thread = AgentThread(
                id=entity.id,
                agent_id=entity.agent_id,
                messages=messages,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
                metadata=json.loads(entity.metadata_json),
            )
            threads.append(thread)
        
        return threads

    async def save_personality(self, personality: AgentPersonality) -> str:
        """Save agent personality and return personality ID."""
        personality_id = str(uuid.uuid4())
        
        entity = AgentPersonalityEntity(
            id=personality_id,
            name=personality.name,
            description=personality.description,
            traits_json=json.dumps(personality.traits),
            mood=personality.mood,
            memory_context=personality.memory_context,
        )
        
        self.session.add(entity)
        await self.session.commit()
        return personality_id

    async def get_personality(self, personality_id: str) -> Optional[AgentPersonality]:
        """Get agent personality by ID."""
        stmt = select(AgentPersonalityEntity).where(AgentPersonalityEntity.id == personality_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return None
        
        return AgentPersonality(
            name=entity.name,
            description=entity.description,
            traits=json.loads(entity.traits_json),
            mood=entity.mood,
            memory_context=entity.memory_context,
        )

    async def update_personality(self, personality_id: str, personality: AgentPersonality) -> bool:
        """Update agent personality."""
        stmt = select(AgentPersonalityEntity).where(AgentPersonalityEntity.id == personality_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        entity.name = personality.name
        entity.description = personality.description
        entity.traits_json = json.dumps(personality.traits)
        entity.mood = personality.mood
        entity.memory_context = personality.memory_context
        entity.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return True

    async def delete_personality(self, personality_id: str) -> bool:
        """Delete agent personality."""
        stmt = select(AgentPersonalityEntity).where(AgentPersonalityEntity.id == personality_id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        await self.session.delete(entity)
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
            agent = Agent(
                model=config.model_name,
                system_prompt=config.system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            self._active_agents[agent_id] = agent
        
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