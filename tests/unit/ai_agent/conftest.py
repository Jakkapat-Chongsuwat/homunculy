"""
Test configuration and fixtures for AI Agent tests.

This module provides test containers and fixtures for testing AI agent functionality
with real databases (MongoDB and Redis) using testcontainers.
"""

import asyncio
import uuid
from typing import AsyncGenerator, Generator

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from models.ai_agent.ai_agent import AgentConfiguration, AgentPersonality, AgentProvider
from repositories.document_db.ai_agent.repository import MongoDBAIAgentRepository
from repositories.key_value_db.ai_agent.repository import RedisAIAgentRepository
from src.di.unit_of_work import MongoDBAIAgentUnitOfWork, RedisAIAgentUnitOfWork


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mongodb_container() -> Generator[MongoDbContainer, None, None]:
    """Start a MongoDB container for testing."""
    with MongoDbContainer("mongo:6").with_exposed_ports(27017) as mongo:
        yield mongo


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    """Start a Redis container for testing."""
    with RedisContainer("redis:7").with_exposed_ports(6379) as redis:
        yield redis


@pytest.fixture(scope="session")
async def mongodb_client(mongodb_container: MongoDbContainer) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create MongoDB client connected to test container."""
    connection_string = mongodb_container.get_connection_url()
    client = AsyncIOMotorClient(connection_string)

    # Wait for connection
    await client.admin.command('ping')

    yield client

    # Cleanup
    client.close()


@pytest.fixture(scope="session")
async def redis_client(redis_container: RedisContainer) -> AsyncGenerator[Redis, None]:
    """Create Redis client connected to test container."""
    # Get connection details from container
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    connection_string = f"redis://{host}:{port}"

    client = Redis.from_url(connection_string)

    # Test connection
    await client.ping()

    yield client

    # Cleanup - use close() instead of aclose()
    await client.close()


@pytest.fixture
async def mongodb_ai_agent_repo(mongodb_client: AsyncIOMotorClient) -> MongoDBAIAgentRepository:
    """Create MongoDB AI agent repository for testing."""
    # Use a unique database for each test to avoid conflicts
    db_name = f"test_ai_agent_{uuid.uuid4().hex[:8]}"
    db = mongodb_client[db_name]
    collection = db.ai_agents

    return MongoDBAIAgentRepository(collection)


@pytest.fixture
async def redis_ai_agent_repo(redis_client: Redis) -> RedisAIAgentRepository:
    """Create Redis AI agent repository for testing."""
    return RedisAIAgentRepository(redis_client)


@pytest.fixture
async def mongodb_ai_agent_uow(mongodb_client: AsyncIOMotorClient) -> MongoDBAIAgentUnitOfWork:
    """Create MongoDB AI agent Unit of Work for testing."""
    # Use a unique database for each test
    db_name = f"test_ai_agent_uow_{uuid.uuid4().hex[:8]}"
    db = mongodb_client[db_name]
    collection = db.ai_agents

    repo = MongoDBAIAgentRepository(collection)
    return MongoDBAIAgentUnitOfWork(mongodb_client, repo)


@pytest.fixture
async def redis_ai_agent_uow(redis_client: Redis) -> RedisAIAgentUnitOfWork:
    """Create Redis AI agent Unit of Work for testing."""
    repo = RedisAIAgentRepository(redis_client)
    return RedisAIAgentUnitOfWork(redis_client, repo)


@pytest.fixture
def sample_agent_config() -> AgentConfiguration:
    """Create a sample agent configuration for testing."""
    personality = AgentPersonality(
        name="Test Agent",
        description="A test AI agent for unit testing",
        traits={"helpfulness": 0.9, "creativity": 0.7},
        mood="curious",
        memory_context="Testing AI agent functionality"
    )

    return AgentConfiguration(
        provider=AgentProvider.PYDANTIC_AI,
        model_name="gpt-4",
        personality=personality,
        system_prompt="You are a helpful test assistant.",
        temperature=0.7,
        max_tokens=1000,
        tools=["web_search", "calculator"]
    )


@pytest.fixture
def sample_agent_personality() -> AgentPersonality:
    """Create a sample agent personality for testing."""
    return AgentPersonality(
        name="Updated Test Agent",
        description="An updated test AI agent",
        traits={"helpfulness": 0.8, "accuracy": 0.9},
        mood="focused",
        memory_context="Updated memory context for testing"
    )