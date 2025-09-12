"""
Document Database AI Agent Repository Implementation.

This module provides the concrete repository implementation for AI agents
using MongoDB, following the existing Pokemon repository pattern.
"""

import json
import uuid
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from models.ai_agent.ai_agent import AgentConfiguration, AgentMessage, AgentPersonality, AgentProvider, AgentResponse, AgentStatus, AgentThread
from repositories.abstraction.ai_agent import AbstractAIAgentRepository


class MongoDBAIAgentRepository(AbstractAIAgentRepository):
    """MongoDB repository for AI agents using Motor."""

    def __init__(self, collection: AsyncIOMotorCollection, session=None):
        self.collection = collection
        self.session = session

    async def save_agent_config(self, config: AgentConfiguration) -> str:
        """Save agent configuration and return agent ID."""
        agent_id = str(uuid.uuid4())

        document = {
            "_id": agent_id,
            "provider": config.provider.value,
            "model_name": config.model_name,
            "personality": config.personality.model_dump(),
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "tools": config.tools,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        await self.collection.insert_one(document, session=self.session)
        return agent_id

    async def get_agent_config(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID."""
        document = await self.collection.find_one({"_id": agent_id}, session=self.session)

        if not document:
            return None

        personality = AgentPersonality(**document["personality"])

        return AgentConfiguration(
            provider=AgentProvider(document["provider"]),
            model_name=document["model_name"],
            personality=personality,
            system_prompt=document["system_prompt"],
            temperature=document["temperature"],
            max_tokens=document["max_tokens"],
            tools=document["tools"],
        )

    async def update_agent_config(self, agent_id: str, config: AgentConfiguration) -> bool:
        """Update agent configuration."""
        update_data = {
            "provider": config.provider.value,
            "model_name": config.model_name,
            "personality": config.personality.model_dump(),
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "tools": config.tools,
            "updated_at": datetime.utcnow(),
        }

        result = await self.collection.update_one(
            {"_id": agent_id},
            {"$set": update_data},
            session=self.session
        )

        return result.modified_count > 0

    async def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration."""
        result = await self.collection.delete_one({"_id": agent_id}, session=self.session)
        return result.deleted_count > 0

    async def list_agent_configs(self, limit: int = 50, offset: int = 0) -> List[AgentConfiguration]:
        """List all agent configurations."""
        cursor = self.collection.find(
            {},
            session=self.session
        ).sort("created_at", -1).skip(offset).limit(limit)

        configs = []
        async for document in cursor:
            personality = AgentPersonality(**document["personality"])

            config = AgentConfiguration(
                provider=AgentProvider(document["provider"]),
                model_name=document["model_name"],
                personality=personality,
                system_prompt=document["system_prompt"],
                temperature=document["temperature"],
                max_tokens=document["max_tokens"],
                tools=document["tools"],
            )
            configs.append(config)

        return configs

    async def save_thread(self, thread: AgentThread) -> str:
        """Save conversation thread and return thread ID."""
        # Convert messages to serializable format
        messages_data = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata or {},
            }
            for msg in thread.messages
        ]

        document = {
            "_id": thread.id,
            "agent_id": thread.agent_id,
            "messages": messages_data,
            "created_at": thread.created_at or datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": thread.metadata,
        }

        await self.collection.insert_one(document, session=self.session)
        return thread.id

    async def get_thread(self, thread_id: str) -> Optional[AgentThread]:
        """Get conversation thread by ID."""
        document = await self.collection.find_one({"_id": thread_id}, session=self.session)

        if not document:
            return None

        # Parse messages from stored format
        messages = [
            AgentMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata"),
            )
            for msg_data in document["messages"]
        ]

        return AgentThread(
            id=document["_id"],
            agent_id=document["agent_id"],
            messages=messages,
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            metadata=document["metadata"],
        )

    async def update_thread(self, thread: AgentThread) -> bool:
        """Update conversation thread."""
        # Convert messages to serializable format
        messages_data = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata or {},
            }
            for msg in thread.messages
        ]

        update_data = {
            "messages": messages_data,
            "updated_at": datetime.utcnow(),
            "metadata": thread.metadata,
        }

        result = await self.collection.update_one(
            {"_id": thread.id},
            {"$set": update_data},
            session=self.session
        )

        return result.modified_count > 0

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete conversation thread."""
        result = await self.collection.delete_one({"_id": thread_id}, session=self.session)
        return result.deleted_count > 0

    async def list_threads_by_agent(
        self, agent_id: str, limit: int = 50, offset: int = 0
    ) -> List[AgentThread]:
        """List conversation threads for a specific agent."""
        cursor = self.collection.find(
            {"agent_id": agent_id},
            session=self.session
        ).sort("updated_at", -1).skip(offset).limit(limit)

        threads = []
        async for document in cursor:
            # Parse messages from stored format
            messages = [
                AgentMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data.get("metadata"),
                )
                for msg_data in document["messages"]
            ]

            thread = AgentThread(
                id=document["_id"],
                agent_id=document["agent_id"],
                messages=messages,
                created_at=document["created_at"],
                updated_at=document["updated_at"],
                metadata=document["metadata"],
            )
            threads.append(thread)

        return threads

    async def save_personality(self, personality: AgentPersonality) -> str:
        """Save agent personality and return personality ID."""
        personality_id = str(uuid.uuid4())

        document = {
            "_id": personality_id,
            "name": personality.name,
            "description": personality.description,
            "traits": personality.traits,
            "mood": personality.mood,
            "memory_context": personality.memory_context,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        await self.collection.insert_one(document, session=self.session)
        return personality_id

    async def get_personality(self, personality_id: str) -> Optional[AgentPersonality]:
        """Get agent personality by ID."""
        document = await self.collection.find_one({"_id": personality_id}, session=self.session)

        if not document:
            return None

        return AgentPersonality(
            name=document["name"],
            description=document["description"],
            traits=document["traits"],
            mood=document["mood"],
            memory_context=document["memory_context"],
        )

    async def update_personality(self, personality_id: str, personality: AgentPersonality) -> bool:
        """Update agent personality."""
        update_data = {
            "name": personality.name,
            "description": personality.description,
            "traits": personality.traits,
            "mood": personality.mood,
            "memory_context": personality.memory_context,
            "updated_at": datetime.utcnow(),
        }

        result = await self.collection.update_one(
            {"_id": personality_id},
            {"$set": update_data},
            session=self.session
        )

        return result.modified_count > 0

    async def delete_personality(self, personality_id: str) -> bool:
        """Delete agent personality."""
        result = await self.collection.delete_one({"_id": personality_id}, session=self.session)
        return result.deleted_count > 0

    # AI Execution Methods (following Pokemon pattern where repos handle business logic)
    async def initialize_agent(self, config: AgentConfiguration) -> str:
        """Initialize an AI agent with the given configuration."""
        # For now, just save the config and return the ID
        # TODO: Implement actual PydanticAI initialization
        return await self.save_agent_config(config)

    async def chat(
        self,
        agent_id: str,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> AgentResponse:
        """Send a message to an agent and get response."""
        # TODO: Implement actual PydanticAI chat functionality
        # For now, return a mock response
        return AgentResponse(
            message=f"MongoDB Mock response to: {message}",
            confidence=0.8,
            reasoning="Mock reasoning for MongoDB implementation",
            status=AgentStatus.COMPLETED,
            metadata={"provider": "mongodb", "agent_id": agent_id}
        )

    async def chat_stream(
        self,
        agent_id: str,
        message: str,
        thread_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> AsyncIterator[AgentResponse]:
        """Send a message to an agent and get streaming response."""
        # TODO: Implement actual streaming with PydanticAI
        # For now, yield a single mock response
        yield AgentResponse(
            message=f"MongoDB Mock streaming response to: {message}",
            confidence=0.8,
            reasoning="Mock streaming reasoning for MongoDB implementation",
            status=AgentStatus.COMPLETED,
            metadata={"provider": "mongodb", "agent_id": agent_id, "streaming": True}
        )

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
        return await self.update_agent_config(agent_id, config)

    async def get_thread_history(self, thread_id: str) -> List[AgentMessage]:
        """Get conversation history for a thread."""
        thread = await self.get_thread(thread_id)
        return thread.messages if thread else []

    async def clear_thread_history(self, thread_id: str) -> bool:
        """Clear conversation history for a thread."""
        thread = await self.get_thread(thread_id)
        if not thread:
            return False

        # Clear messages but keep thread structure
        thread.messages = []
        return await self.update_thread(thread)

    async def get_agent_status(self, agent_id: str) -> Dict:
        """Get current status of an agent."""
        config = await self.get_agent_config(agent_id)
        if not config:
            return {"status": "not_found"}

        return {
            "status": "active",
            "agent_id": agent_id,
            "provider": config.provider.value,
            "model": config.model_name,
            "last_updated": datetime.utcnow().isoformat()
        }

    async def shutdown_agent(self, agent_id: str) -> bool:
        """Shutdown a specific agent."""
        # For now, just mark as inactive
        # TODO: Implement actual agent shutdown logic
        return True

    async def list_available_providers(self) -> List[AgentProvider]:
        """List all available AI agent providers."""
        # For MongoDB implementation, return supported providers
        return [AgentProvider.PYDANTIC_AI]