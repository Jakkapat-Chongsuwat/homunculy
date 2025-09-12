"""
Key-Value Database AI Agent Repository Implementation.

This module provides the concrete repository implementation for AI agents
using Redis, following the existing Pokemon repository pattern.
"""

import json
import uuid
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

from redis.asyncio import Redis

from models.ai_agent import AgentConfiguration, AgentMessage, AgentPersonality, AgentProvider, AgentResponse, AgentStatus, AgentThread
from repositories.abstraction.ai_agent import AbstractAIAgentRepository


class RedisAIAgentRepository(AbstractAIAgentRepository):
    """Redis repository for AI agents using redis-py."""

    def __init__(self, client: Redis):
        self.client = client

    async def save_agent_config(self, config: AgentConfiguration) -> str:
        """Save agent configuration and return agent ID."""
        agent_id = str(uuid.uuid4())
        key = f"ai_agent:config:{agent_id}"

        data = {
            "id": agent_id,
            "provider": config.provider.value,
            "model_name": config.model_name,
            "personality": config.personality.model_dump(),
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "tools": config.tools,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self.client.set(key, json.dumps(data))
        return agent_id

    async def get_agent_config(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID."""
        key = f"ai_agent:config:{agent_id}"
        data_str = await self.client.get(key)

        if not data_str:
            return None

        data = json.loads(data_str)
        personality = AgentPersonality(**data["personality"])

        return AgentConfiguration(
            provider=AgentProvider(data["provider"]),
            model_name=data["model_name"],
            personality=personality,
            system_prompt=data["system_prompt"],
            temperature=data["temperature"],
            max_tokens=data["max_tokens"],
            tools=data["tools"],
        )

    async def update_agent_config(self, agent_id: str, config: AgentConfiguration) -> bool:
        """Update agent configuration."""
        key = f"ai_agent:config:{agent_id}"

        # Check if exists
        existing = await self.client.get(key)
        if not existing:
            return False

        data = {
            "id": agent_id,
            "provider": config.provider.value,
            "model_name": config.model_name,
            "personality": config.personality.model_dump(),
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "tools": config.tools,
            "created_at": json.loads(existing)["created_at"],  # Preserve original creation time
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self.client.set(key, json.dumps(data))
        return True

    async def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration."""
        key = f"ai_agent:config:{agent_id}"
        result = await self.client.delete(key)
        return result > 0

    async def list_agent_configs(self, limit: int = 50, offset: int = 0) -> List[AgentConfiguration]:
        """List all agent configurations."""
        # Get all agent config keys
        keys = await self.client.keys("ai_agent:config:*")

        if offset >= len(keys):
            return []

        # Get the requested slice
        end_index = min(offset + limit, len(keys))
        selected_keys = keys[offset:end_index]

        configs = []
        for key in selected_keys:
            data_str = await self.client.get(key)
            if data_str:
                data = json.loads(data_str)
                personality = AgentPersonality(**data["personality"])

                config = AgentConfiguration(
                    provider=AgentProvider(data["provider"]),
                    model_name=data["model_name"],
                    personality=personality,
                    system_prompt=data["system_prompt"],
                    temperature=data["temperature"],
                    max_tokens=data["max_tokens"],
                    tools=data["tools"],
                )
                configs.append(config)

        return configs

    async def save_thread(self, thread: AgentThread) -> str:
        """Save conversation thread and return thread ID."""
        key = f"ai_agent:thread:{thread.id}"

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

        data = {
            "id": thread.id,
            "agent_id": thread.agent_id,
            "messages": messages_data,
            "created_at": (thread.created_at or datetime.utcnow()).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": thread.metadata,
        }

        await self.client.set(key, json.dumps(data))
        return thread.id

    async def get_thread(self, thread_id: str) -> Optional[AgentThread]:
        """Get conversation thread by ID."""
        key = f"ai_agent:thread:{thread_id}"
        data_str = await self.client.get(key)

        if not data_str:
            return None

        data = json.loads(data_str)

        # Parse messages from stored format
        messages = [
            AgentMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata"),
            )
            for msg_data in data["messages"]
        ]

        return AgentThread(
            id=data["id"],
            agent_id=data["agent_id"],
            messages=messages,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data["metadata"],
        )

    async def update_thread(self, thread: AgentThread) -> bool:
        """Update conversation thread."""
        key = f"ai_agent:thread:{thread.id}"

        # Check if exists
        existing = await self.client.get(key)
        if not existing:
            return False

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

        data = {
            "id": thread.id,
            "agent_id": thread.agent_id,
            "messages": messages_data,
            "created_at": json.loads(existing)["created_at"],  # Preserve original creation time
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": thread.metadata,
        }

        await self.client.set(key, json.dumps(data))
        return True

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete conversation thread."""
        key = f"ai_agent:thread:{thread_id}"
        result = await self.client.delete(key)
        return result > 0

    async def list_threads_by_agent(
        self, agent_id: str, limit: int = 50, offset: int = 0
    ) -> List[AgentThread]:
        """List conversation threads for a specific agent."""
        # Get all thread keys for this agent
        keys = await self.client.keys("ai_agent:thread:*")

        agent_threads = []
        for key in keys:
            data_str = await self.client.get(key)
            if data_str:
                data = json.loads(data_str)
                if data["agent_id"] == agent_id:
                    agent_threads.append((key, data))

        if offset >= len(agent_threads):
            return []

        # Sort by updated_at descending
        agent_threads.sort(key=lambda x: x[1]["updated_at"], reverse=True)

        # Get the requested slice
        end_index = min(offset + limit, len(agent_threads))
        selected_threads = agent_threads[offset:end_index]

        threads = []
        for _, data in selected_threads:
            # Parse messages from stored format
            messages = [
                AgentMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data.get("metadata"),
                )
                for msg_data in data["messages"]
            ]

            thread = AgentThread(
                id=data["id"],
                agent_id=data["agent_id"],
                messages=messages,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                metadata=data["metadata"],
            )
            threads.append(thread)

        return threads

    async def save_personality(self, personality: AgentPersonality) -> str:
        """Save agent personality and return personality ID."""
        personality_id = str(uuid.uuid4())
        key = f"ai_agent:personality:{personality_id}"

        data = {
            "id": personality_id,
            "name": personality.name,
            "description": personality.description,
            "traits": personality.traits,
            "mood": personality.mood,
            "memory_context": personality.memory_context,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self.client.set(key, json.dumps(data))
        return personality_id

    async def get_personality(self, personality_id: str) -> Optional[AgentPersonality]:
        """Get agent personality by ID."""
        key = f"ai_agent:personality:{personality_id}"
        data_str = await self.client.get(key)

        if not data_str:
            return None

        data = json.loads(data_str)

        return AgentPersonality(
            name=data["name"],
            description=data["description"],
            traits=data["traits"],
            mood=data["mood"],
            memory_context=data["memory_context"],
        )

    async def update_personality(self, personality_id: str, personality: AgentPersonality) -> bool:
        """Update agent personality."""
        key = f"ai_agent:personality:{personality_id}"

        # Check if exists
        existing = await self.client.get(key)
        if not existing:
            return False

        data = {
            "id": personality_id,
            "name": personality.name,
            "description": personality.description,
            "traits": personality.traits,
            "mood": personality.mood,
            "memory_context": personality.memory_context,
            "created_at": json.loads(existing)["created_at"],  # Preserve original creation time
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self.client.set(key, json.dumps(data))
        return True

    async def delete_personality(self, personality_id: str) -> bool:
        """Delete agent personality."""
        key = f"ai_agent:personality:{personality_id}"
        result = await self.client.delete(key)
        return result > 0

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
            message=f"Redis Mock response to: {message}",
            confidence=0.8,
            reasoning="Mock reasoning for Redis implementation",
            status=AgentStatus.COMPLETED,
            metadata={"provider": "redis", "agent_id": agent_id}
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
            message=f"Redis Mock streaming response to: {message}",
            confidence=0.8,
            reasoning="Mock streaming reasoning for Redis implementation",
            status=AgentStatus.COMPLETED,
            metadata={"provider": "redis", "agent_id": agent_id, "streaming": True}
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
        # For Redis implementation, return supported providers
        return [AgentProvider.PYDANTIC_AI]