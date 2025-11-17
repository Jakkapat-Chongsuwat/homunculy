"""
Integration tests for AI Agent Unit of Work implementations.

These tests verify that the Unit of Work pattern works correctly with
real database containers, ensuring proper transaction management and
data consistency.
"""

import uuid
from datetime import datetime, timezone

import pytest

from models.ai_agent.ai_agent import AgentConfiguration, AgentMessage, AgentPersonality, AgentProvider, AgentThread
from src.di.unit_of_work import MongoDBAIAgentUnitOfWork, RedisAIAgentUnitOfWork


class TestMongoDBAIAgentUnitOfWork:
    """Integration tests for MongoDB AI Agent Unit of Work."""

    @pytest.mark.asyncio
    async def test_context_manager_success(self, mongodb_ai_agent_uow: MongoDBAIAgentUnitOfWork, sample_agent_config: AgentConfiguration):
        """Test successful transaction with context manager."""
        async with mongodb_ai_agent_uow:
            # Perform operations within the transaction
            agent_id = await mongodb_ai_agent_uow.ai_agent_repo.save_agent_config(sample_agent_config)

            # Create a thread for the agent
            thread = AgentThread(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                messages=[
                    AgentMessage(
                        role="user",
                        content="Test message",
                        timestamp=datetime.now(timezone.utc)
                    )
                ]
            )
            await mongodb_ai_agent_uow.ai_agent_repo.save_thread(thread)

        # After context manager exits, verify data was committed
        config = await mongodb_ai_agent_uow.ai_agent_repo.get_agent_config(agent_id)
        assert config is not None
        assert config.personality.name == sample_agent_config.personality.name

    @pytest.mark.asyncio
    async def test_context_manager_failure_rollback(self, mongodb_ai_agent_uow: MongoDBAIAgentUnitOfWork, sample_agent_config: AgentConfiguration):
        """Test transaction rollback on failure."""
        agent_id = None
        try:
            async with mongodb_ai_agent_uow:
                # Perform operations
                agent_id = await mongodb_ai_agent_uow.ai_agent_repo.save_agent_config(sample_agent_config)

                # Simulate failure
                raise ValueError("Simulated failure")
        except ValueError:
            pass  # Expected exception

        # Verify rollback - data should not be persisted
        if agent_id:
            config = await mongodb_ai_agent_uow.ai_agent_repo.get_agent_config(agent_id)
            assert config is None  # Should be None due to rollback

    @pytest.mark.asyncio
    async def test_multiple_operations_in_transaction(self, mongodb_ai_agent_uow: MongoDBAIAgentUnitOfWork, sample_agent_config: AgentConfiguration, sample_agent_personality: AgentPersonality):
        """Test multiple related operations in a single transaction."""
        async with mongodb_ai_agent_uow:
            # Create agent
            agent_id = await mongodb_ai_agent_uow.ai_agent_repo.save_agent_config(sample_agent_config)

            # Save personality
            personality_id = await mongodb_ai_agent_uow.ai_agent_repo.save_personality(sample_agent_personality)

            # Create thread linking them
            thread = AgentThread(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                messages=[
                    AgentMessage(
                        role="system",
                        content=f"Agent {agent_id} initialized with personality {personality_id}",
                        timestamp=datetime.now(timezone.utc)
                    )
                ]
            )
            thread_id = await mongodb_ai_agent_uow.ai_agent_repo.save_thread(thread)

        # Verify all operations were committed
        config = await mongodb_ai_agent_uow.ai_agent_repo.get_agent_config(agent_id)
        assert config is not None

        personality = await mongodb_ai_agent_uow.ai_agent_repo.get_personality(personality_id)
        assert personality is not None

        saved_thread = await mongodb_ai_agent_uow.ai_agent_repo.get_thread(thread_id)
        assert saved_thread is not None
        assert saved_thread.agent_id == agent_id

    @pytest.mark.asyncio
    async def test_commit_method_interface(self, mongodb_ai_agent_uow: MongoDBAIAgentUnitOfWork):
        """Test that commit method exists for interface compliance."""
        # The commit method should exist but may be a no-op for MongoDB
        assert hasattr(mongodb_ai_agent_uow, 'commit')
        mongodb_ai_agent_uow.commit()  # Should not raise exception

    @pytest.mark.asyncio
    async def test_rollback_method_interface(self, mongodb_ai_agent_uow: MongoDBAIAgentUnitOfWork):
        """Test that rollback method exists for interface compliance."""
        # The rollback method should exist but may be a no-op for MongoDB
        assert hasattr(mongodb_ai_agent_uow, 'rollback')
        mongodb_ai_agent_uow.rollback()  # Should not raise exception


class TestRedisAIAgentUnitOfWork:
    """Integration tests for Redis AI Agent Unit of Work."""

    @pytest.mark.asyncio
    async def test_context_manager_success(self, redis_ai_agent_uow: RedisAIAgentUnitOfWork, sample_agent_config: AgentConfiguration):
        """Test successful operations with Redis (no real transactions)."""
        async with redis_ai_agent_uow:
            # Perform operations within the context
            agent_id = await redis_ai_agent_uow.ai_agent_repo.save_agent_config(sample_agent_config)

            # Create a thread for the agent
            thread = AgentThread(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                messages=[
                    AgentMessage(
                        role="user",
                        content="Test message for Redis",
                        timestamp=datetime.now(timezone.utc)
                    )
                ]
            )
            await redis_ai_agent_uow.ai_agent_repo.save_thread(thread)

        # After context manager exits, verify data was persisted
        config = await redis_ai_agent_uow.ai_agent_repo.get_agent_config(agent_id)
        assert config is not None
        assert config.personality.name == sample_agent_config.personality.name

    @pytest.mark.asyncio
    async def test_multiple_operations_redis(self, redis_ai_agent_uow: RedisAIAgentUnitOfWork, sample_agent_config: AgentConfiguration, sample_agent_personality: AgentPersonality):
        """Test multiple operations with Redis."""
        async with redis_ai_agent_uow:
            # Create agent
            agent_id = await redis_ai_agent_uow.ai_agent_repo.save_agent_config(sample_agent_config)

            # Save personality
            personality_id = await redis_ai_agent_uow.ai_agent_repo.save_personality(sample_agent_personality)

            # Create thread linking them
            thread = AgentThread(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                messages=[
                    AgentMessage(
                        role="system",
                        content=f"Redis Agent {agent_id} initialized with personality {personality_id}",
                        timestamp=datetime.now(timezone.utc)
                    )
                ]
            )
            thread_id = await redis_ai_agent_uow.ai_agent_repo.save_thread(thread)

        # Verify all operations were persisted
        config = await redis_ai_agent_uow.ai_agent_repo.get_agent_config(agent_id)
        assert config is not None

        personality = await redis_ai_agent_uow.ai_agent_repo.get_personality(personality_id)
        assert personality is not None

        saved_thread = await redis_ai_agent_uow.ai_agent_repo.get_thread(thread_id)
        assert saved_thread is not None
        assert saved_thread.agent_id == agent_id

    @pytest.mark.asyncio
    async def test_commit_method_interface_redis(self, redis_ai_agent_uow: RedisAIAgentUnitOfWork):
        """Test that commit method exists for Redis UoW."""
        assert hasattr(redis_ai_agent_uow, 'commit')
        redis_ai_agent_uow.commit()  # Should not raise exception

    @pytest.mark.asyncio
    async def test_rollback_method_interface_redis(self, redis_ai_agent_uow: RedisAIAgentUnitOfWork):
        """Test that rollback method exists for Redis UoW."""
        assert hasattr(redis_ai_agent_uow, 'rollback')
        redis_ai_agent_uow.rollback()  # Should not raise exception


class TestUnitOfWorkIsolation:
    """Test isolation between different Unit of Work instances."""

    @pytest.mark.asyncio
    async def test_mongodb_isolation(self, mongodb_client):
        """Test that different UoW instances use isolated databases."""
        from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository

        # Create two separate UoW instances with different databases
        db1 = mongodb_client["test_isolation_1"]
        db2 = mongodb_client["test_isolation_2"]

        repo1 = MongoDBAIAgentRepository(db1.ai_agents)
        repo2 = MongoDBAIAgentRepository(db2.ai_agents)

        uow1 = MongoDBAIAgentUnitOfWork(mongodb_client, repo1)
        uow2 = MongoDBAIAgentUnitOfWork(mongodb_client, repo2)

        # Create agent in first UoW
        config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(name="Isolation Test Agent", description="Test agent for isolation")
        )

        async with uow1:
            agent_id = await uow1.ai_agent_repo.save_agent_config(config)

        # Verify agent exists in first database but not second
        config1 = await uow1.ai_agent_repo.get_agent_config(agent_id)
        config2 = await uow2.ai_agent_repo.get_agent_config(agent_id)

        assert config1 is not None
        assert config2 is None  # Should not exist in second database

    @pytest.mark.asyncio
    async def test_redis_isolation(self, redis_client):
        """Test that Redis operations are properly isolated."""
        from repositories.key_value_db.ai_agent.repository import RedisAIAgentRepository

        # Create two separate repository instances
        repo1 = RedisAIAgentRepository(redis_client)
        repo2 = RedisAIAgentRepository(redis_client)

        uow1 = RedisAIAgentUnitOfWork(redis_client, repo1)
        uow2 = RedisAIAgentUnitOfWork(redis_client, repo2)

        # Create agent in first UoW
        config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(name="Redis Isolation Test", description="Redis test agent for isolation")
        )

        async with uow1:
            agent_id = await uow1.ai_agent_repo.save_agent_config(config)

        # Both should be able to access the same data (Redis is shared)
        config1 = await uow1.ai_agent_repo.get_agent_config(agent_id)
        config2 = await uow2.ai_agent_repo.get_agent_config(agent_id)

        assert config1 is not None
        assert config2 is not None  # Both can access (Redis is shared storage)
        assert config1.personality.name == config2.personality.name