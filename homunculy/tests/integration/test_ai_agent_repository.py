"""
Integration tests for AI Agent Repository implementations.

These tests use real database containers (MongoDB and Redis) to test
the repository implementations with actual database operations.
"""

import uuid
from datetime import datetime, timezone

import pytest

from models.ai_agent.ai_agent import AgentConfiguration, AgentMessage, AgentPersonality, AgentProvider, AgentThread
from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository
from repositories.key_value_db.ai_agent.repository import RedisAIAgentRepository


class TestMongoDBAIAgentRepository:
    """Integration tests for MongoDB AI Agent Repository."""

    @pytest.mark.asyncio
    async def test_save_and_get_agent_config(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test saving and retrieving agent configuration."""
        # Save configuration
        agent_id = await mongodb_ai_agent_repo.save_agent_config(sample_agent_config)
        assert agent_id is not None
        assert isinstance(agent_id, str)

        # Retrieve configuration
        retrieved_config = await mongodb_ai_agent_repo.get_agent_config(agent_id)
        assert retrieved_config is not None
        assert retrieved_config.provider == sample_agent_config.provider
        assert retrieved_config.model_name == sample_agent_config.model_name
        assert retrieved_config.personality.name == sample_agent_config.personality.name

    @pytest.mark.asyncio
    async def test_update_agent_config(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test updating agent configuration."""
        # Save initial configuration
        agent_id = await mongodb_ai_agent_repo.save_agent_config(sample_agent_config)

        # Update configuration
        updated_config = sample_agent_config.model_copy()
        updated_config.model_name = "gpt-3.5-turbo"

        success = await mongodb_ai_agent_repo.update_agent_config(agent_id, updated_config)
        assert success is True

        # Verify update
        retrieved_config = await mongodb_ai_agent_repo.get_agent_config(agent_id)
        assert retrieved_config is not None
        assert retrieved_config.model_name == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_delete_agent_config(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test deleting agent configuration."""
        # Save configuration
        agent_id = await mongodb_ai_agent_repo.save_agent_config(sample_agent_config)

        # Delete configuration
        success = await mongodb_ai_agent_repo.delete_agent_config(agent_id)
        assert success is True

        # Verify deletion
        retrieved_config = await mongodb_ai_agent_repo.get_agent_config(agent_id)
        assert retrieved_config is None

    @pytest.mark.asyncio
    async def test_list_agent_configs(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test listing agent configurations."""
        # Save multiple configurations
        agent_ids = []
        for i in range(3):
            config = sample_agent_config.model_copy()
            config.personality.name = f"Test Agent {i}"
            agent_id = await mongodb_ai_agent_repo.save_agent_config(config)
            agent_ids.append(agent_id)

        # List configurations
        configs = await mongodb_ai_agent_repo.list_agent_configs(limit=10)
        assert len(configs) >= 3

        # Verify our saved configs are in the list
        saved_names = {config.personality.name for config in configs}
        assert "Test Agent 0" in saved_names
        assert "Test Agent 1" in saved_names
        assert "Test Agent 2" in saved_names

    @pytest.mark.asyncio
    async def test_thread_operations(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository):
        """Test thread creation, retrieval, and updates."""
        agent_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        # Create thread
        thread = AgentThread(
            id=thread_id,
            agent_id=agent_id,
            messages=[
                AgentMessage(
                    role="user",
                    content="Hello",
                    timestamp=datetime.now(timezone.utc)
                ),
                AgentMessage(
                    role="assistant",
                    content="Hi there!",
                    timestamp=datetime.now(timezone.utc)
                )
            ]
        )

        # Save thread
        saved_id = await mongodb_ai_agent_repo.save_thread(thread)
        assert saved_id == thread_id

        # Retrieve thread
        retrieved_thread = await mongodb_ai_agent_repo.get_thread(thread_id)
        assert retrieved_thread is not None
        assert retrieved_thread.id == thread_id
        assert retrieved_thread.agent_id == agent_id
        assert len(retrieved_thread.messages) == 2
        assert retrieved_thread.messages[0].content == "Hello"
        assert retrieved_thread.messages[1].content == "Hi there!"

    @pytest.mark.asyncio
    async def test_personality_operations(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_personality: AgentPersonality):
        """Test personality creation, retrieval, and updates."""
        # Save personality
        personality_id = await mongodb_ai_agent_repo.save_personality(sample_agent_personality)
        assert personality_id is not None

        # Retrieve personality
        retrieved_personality = await mongodb_ai_agent_repo.get_personality(personality_id)
        assert retrieved_personality is not None
        assert retrieved_personality.name == sample_agent_personality.name
        assert retrieved_personality.traits == sample_agent_personality.traits

        # Update personality
        updated_personality = sample_agent_personality.model_copy()
        updated_personality.mood = "excited"

        success = await mongodb_ai_agent_repo.update_personality(personality_id, updated_personality)
        assert success is True

        # Verify update
        retrieved_updated = await mongodb_ai_agent_repo.get_personality(personality_id)
        assert retrieved_updated is not None
        assert retrieved_updated.mood == "excited"

    @pytest.mark.asyncio
    async def test_initialize_agent(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test agent initialization."""
        agent_id = await mongodb_ai_agent_repo.initialize_agent(sample_agent_config)
        assert agent_id is not None

        # Verify agent was created
        config = await mongodb_ai_agent_repo.get_agent_config(agent_id)
        assert config is not None
        assert config.provider == sample_agent_config.provider

    @pytest.mark.asyncio
    async def test_chat_functionality(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test chat functionality."""
        # Initialize agent first
        agent_id = await mongodb_ai_agent_repo.initialize_agent(sample_agent_config)

        # Test chat
        response = await mongodb_ai_agent_repo.chat(agent_id, "Hello, how are you?")
        assert response is not None
        assert hasattr(response, 'message')
        assert hasattr(response, 'confidence')
        assert "MongoDB Mock response" in response.message

    @pytest.mark.asyncio
    async def test_agent_status(self, mongodb_ai_agent_repo: MongoDBAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test getting agent status."""
        # Initialize agent
        agent_id = await mongodb_ai_agent_repo.initialize_agent(sample_agent_config)

        # Get status
        status = await mongodb_ai_agent_repo.get_agent_status(agent_id)
        assert status is not None
        assert status["status"] == "active"
        assert status["agent_id"] == agent_id


class TestRedisAIAgentRepository:
    """Integration tests for Redis AI Agent Repository."""

    @pytest.mark.asyncio
    async def test_save_and_get_agent_config(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test saving and retrieving agent configuration."""
        # Save configuration
        agent_id = await redis_ai_agent_repo.save_agent_config(sample_agent_config)
        assert agent_id is not None
        assert isinstance(agent_id, str)

        # Retrieve configuration
        retrieved_config = await redis_ai_agent_repo.get_agent_config(agent_id)
        assert retrieved_config is not None
        assert retrieved_config.provider == sample_agent_config.provider
        assert retrieved_config.model_name == sample_agent_config.model_name
        assert retrieved_config.personality.name == sample_agent_config.personality.name

    @pytest.mark.asyncio
    async def test_update_agent_config(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test updating agent configuration."""
        # Save initial configuration
        agent_id = await redis_ai_agent_repo.save_agent_config(sample_agent_config)

        # Update configuration
        updated_config = sample_agent_config.model_copy()
        updated_config.model_name = "gpt-3.5-turbo"

        success = await redis_ai_agent_repo.update_agent_config(agent_id, updated_config)
        assert success is True

        # Verify update
        retrieved_config = await redis_ai_agent_repo.get_agent_config(agent_id)
        assert retrieved_config is not None
        assert retrieved_config.model_name == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_delete_agent_config(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test deleting agent configuration."""
        # Save configuration
        agent_id = await redis_ai_agent_repo.save_agent_config(sample_agent_config)

        # Delete configuration
        success = await redis_ai_agent_repo.delete_agent_config(agent_id)
        assert success is True

        # Verify deletion
        retrieved_config = await redis_ai_agent_repo.get_agent_config(agent_id)
        assert retrieved_config is None

    @pytest.mark.asyncio
    async def test_list_agent_configs(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test listing agent configurations."""
        # Save multiple configurations
        agent_ids = []
        for i in range(3):
            config = sample_agent_config.model_copy()
            config.personality.name = f"Redis Test Agent {i}"
            agent_id = await redis_ai_agent_repo.save_agent_config(config)
            agent_ids.append(agent_id)

        # List configurations
        configs = await redis_ai_agent_repo.list_agent_configs(limit=10)
        assert len(configs) >= 3

        # Verify our saved configs are in the list
        saved_names = {config.personality.name for config in configs}
        assert "Redis Test Agent 0" in saved_names
        assert "Redis Test Agent 1" in saved_names
        assert "Redis Test Agent 2" in saved_names

    @pytest.mark.asyncio
    async def test_thread_operations(self, redis_ai_agent_repo: RedisAIAgentRepository):
        """Test thread creation, retrieval, and updates."""
        agent_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())

        # Create thread
        thread = AgentThread(
            id=thread_id,
            agent_id=agent_id,
            messages=[
                AgentMessage(
                    role="user",
                    content="Hello from Redis",
                    timestamp=datetime.now(timezone.utc)
                ),
                AgentMessage(
                    role="assistant",
                    content="Hi from Redis!",
                    timestamp=datetime.now(timezone.utc)
                )
            ]
        )

        # Save thread
        saved_id = await redis_ai_agent_repo.save_thread(thread)
        assert saved_id == thread_id

        # Retrieve thread
        retrieved_thread = await redis_ai_agent_repo.get_thread(thread_id)
        assert retrieved_thread is not None
        assert retrieved_thread.id == thread_id
        assert retrieved_thread.agent_id == agent_id
        assert len(retrieved_thread.messages) == 2
        assert retrieved_thread.messages[0].content == "Hello from Redis"
        assert retrieved_thread.messages[1].content == "Hi from Redis!"

    @pytest.mark.asyncio
    async def test_personality_operations(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_personality: AgentPersonality):
        """Test personality creation, retrieval, and updates."""
        # Save personality
        personality_id = await redis_ai_agent_repo.save_personality(sample_agent_personality)
        assert personality_id is not None

        # Retrieve personality
        retrieved_personality = await redis_ai_agent_repo.get_personality(personality_id)
        assert retrieved_personality is not None
        assert retrieved_personality.name == sample_agent_personality.name
        assert retrieved_personality.traits == sample_agent_personality.traits

        # Update personality
        updated_personality = sample_agent_personality.model_copy()
        updated_personality.mood = "calm"

        success = await redis_ai_agent_repo.update_personality(personality_id, updated_personality)
        assert success is True

        # Verify update
        retrieved_updated = await redis_ai_agent_repo.get_personality(personality_id)
        assert retrieved_updated is not None
        assert retrieved_updated.mood == "calm"

    @pytest.mark.asyncio
    async def test_initialize_agent(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test agent initialization."""
        agent_id = await redis_ai_agent_repo.initialize_agent(sample_agent_config)
        assert agent_id is not None

        # Verify agent was created
        config = await redis_ai_agent_repo.get_agent_config(agent_id)
        assert config is not None
        assert config.provider == sample_agent_config.provider

    @pytest.mark.asyncio
    async def test_chat_functionality(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test chat functionality."""
        # Initialize agent first
        agent_id = await redis_ai_agent_repo.initialize_agent(sample_agent_config)

        # Test chat
        response = await redis_ai_agent_repo.chat(agent_id, "Hello from Redis!")
        assert response is not None
        assert hasattr(response, 'message')
        assert hasattr(response, 'confidence')
        assert "Redis Mock response" in response.message

    @pytest.mark.asyncio
    async def test_agent_status(self, redis_ai_agent_repo: RedisAIAgentRepository, sample_agent_config: AgentConfiguration):
        """Test getting agent status."""
        # Initialize agent
        agent_id = await redis_ai_agent_repo.initialize_agent(sample_agent_config)

        # Get status
        status = await redis_ai_agent_repo.get_agent_status(agent_id)
        assert status is not None
        assert status["status"] == "active"
        assert status["agent_id"] == agent_id