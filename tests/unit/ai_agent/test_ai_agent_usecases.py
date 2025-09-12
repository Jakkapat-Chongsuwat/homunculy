"""
Unit tests fofrom src.usecases.ai_agent import (
    initialize_ai_agent,
    chat_with_agent,
    update_agent_personality,
    get_agent_configuration,
    get_agent_status,
    shutdown_agent,
    list_available_providers
)t use cases.

These tests validate the AI agent use cases following Clean Architecture patterns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, Dict

from src.models.ai_agent import (
    AgentProvider,
    AgentStatus,
    AgentPersonality,
    AgentConfiguration,
    AgentResponse
)
from src.di.unit_of_work import AbstractUnitOfWork
from usecases.ai_agent import (
    initialize_ai_agent,
    chat_with_agent,
    update_agent_personality,
    get_agent_configuration,
    get_agent_status,
    shutdown_agent,
    list_available_providers
)


class TestInitializeAIAgent:
    """Test initialize_ai_agent use case."""

    @pytest.fixture
    def agent_config(self):
        """Create test agent configuration."""
        personality = AgentPersonality(
            name="Test Agent",
            description="Test agent for unit testing",
            traits={"helpfulness": 0.9}
        )
        return AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=personality,
            system_prompt="You are a test assistant"
        )

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.initialize_agent = AsyncMock(return_value="test-agent-id")
        return uow

    @pytest.mark.asyncio
    async def test_initialize_ai_agent_success(self, agent_config, mock_uow):
        """Test successful agent initialization."""
        result = await initialize_ai_agent(mock_uow, agent_config)

        assert result == "test-agent-id"
        mock_uow.ai_agent_repo.initialize_agent.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_initialize_ai_agent_calls_uow_context(self, agent_config, mock_uow):
        """Test that initialize_ai_agent uses unit of work context manager."""
        await initialize_ai_agent(mock_uow, agent_config)

        mock_uow.__aenter__.assert_called_once()
        mock_uow.__aexit__.assert_called_once()


class TestChatWithAgent:
    """Test chat_with_agent use case."""

    @pytest.fixture
    def mock_response(self):
        """Create mock agent response."""
        return AgentResponse(
            message="Test response",
            confidence=0.8,
            reasoning="Test reasoning"
        )

    @pytest.fixture
    def mock_uow(self, mock_response):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.chat = AsyncMock(return_value=mock_response)
        return uow

    @pytest.mark.asyncio
    async def test_chat_with_agent_success(self, mock_uow, mock_response):
        """Test successful chat with agent."""
        result = await chat_with_agent(mock_uow, "agent-123", "Hello")

        assert result == mock_response
        mock_uow.ai_agent_repo.chat.assert_called_once_with("agent-123", "Hello", None, None)

    @pytest.mark.asyncio
    async def test_chat_with_agent_with_thread_and_context(self, mock_uow, mock_response):
        """Test chat with agent including thread and context."""
        context = {"session_id": "test"}
        result = await chat_with_agent(
            mock_uow,
            "agent-123",
            "Hello",
            thread_id="thread-456",
            context=context
        )

        assert result == mock_response
        mock_uow.ai_agent_repo.chat.assert_called_once_with("agent-123", "Hello", "thread-456", context)


class TestUpdateAgentPersonality:
    """Test update_agent_personality use case."""

    @pytest.fixture
    def personality(self):
        """Create test personality."""
        return AgentPersonality(
            name="Updated Agent",
            description="Updated test agent",
            traits={"creativity": 0.8}
        )

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.update_agent_personality = AsyncMock(return_value=True)
        return uow

    @pytest.mark.asyncio
    async def test_update_agent_personality_success(self, mock_uow, personality):
        """Test successful personality update."""
        result = await update_agent_personality(mock_uow, "agent-123", personality)

        assert result is True
        mock_uow.ai_agent_repo.update_agent_personality.assert_called_once_with("agent-123", personality)


class TestGetAgentConfiguration:
    """Test get_agent_configuration use case."""

    @pytest.fixture
    def agent_config(self):
        """Create test agent configuration."""
        personality = AgentPersonality(name="Test", description="Test personality")
        return AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=personality
        )

    @pytest.fixture
    def mock_uow(self, agent_config):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.get_agent_config = AsyncMock(return_value=agent_config)
        return uow

    @pytest.mark.asyncio
    async def test_get_agent_configuration_success(self, mock_uow, agent_config):
        """Test successful configuration retrieval."""
        result = await get_agent_configuration(mock_uow, "agent-123")

        assert result == agent_config
        mock_uow.ai_agent_repo.get_agent_config.assert_called_once_with("agent-123")

    @pytest.mark.asyncio
    async def test_get_agent_configuration_not_found(self, mock_uow):
        """Test configuration retrieval when agent not found."""
        mock_uow.ai_agent_repo.get_agent_config = AsyncMock(return_value=None)

        result = await get_agent_configuration(mock_uow, "agent-123")

        assert result is None


class TestGetAgentStatus:
    """Test get_agent_status use case."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.get_agent_status = AsyncMock(return_value={"status": "active"})
        return uow

    @pytest.mark.asyncio
    async def test_get_agent_status_success(self, mock_uow):
        """Test successful status retrieval."""
        result = await get_agent_status(mock_uow, "agent-123")

        assert result == {"status": "active"}
        mock_uow.ai_agent_repo.get_agent_status.assert_called_once_with("agent-123")


class TestShutdownAgent:
    """Test shutdown_agent use case."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.shutdown_agent = AsyncMock(return_value=True)
        return uow

    @pytest.mark.asyncio
    async def test_shutdown_agent_success(self, mock_uow):
        """Test successful agent shutdown."""
        result = await shutdown_agent(mock_uow, "agent-123")

        assert result is True
        mock_uow.ai_agent_repo.shutdown_agent.assert_called_once_with("agent-123")


class TestListAvailableProviders:
    """Test list_available_providers use case."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()
        uow.ai_agent_repo.list_available_providers = AsyncMock(return_value=[AgentProvider.PYDANTIC_AI])
        return uow

    @pytest.mark.asyncio
    async def test_list_available_providers_success(self, mock_uow):
        """Test successful provider listing."""
        result = await list_available_providers(mock_uow)

        assert result == [AgentProvider.PYDANTIC_AI]
        mock_uow.ai_agent_repo.list_available_providers.assert_called_once()


class TestUseCaseIntegration:
    """Integration tests for use case functions."""

    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle(self):
        """Test complete agent lifecycle through use cases."""
        # Create configuration
        personality = AgentPersonality(
            name="Lifecycle Test Agent",
            description="Agent for lifecycle testing"
        )
        config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=personality
        )

        # Create mock UOW
        uow = MagicMock(spec=AbstractUnitOfWork)
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.ai_agent_repo = MagicMock()

        # Mock all repository methods
        uow.ai_agent_repo.initialize_agent = AsyncMock(return_value="lifecycle-agent-id")
        uow.ai_agent_repo.get_agent_config = AsyncMock(return_value=config)
        uow.ai_agent_repo.chat = AsyncMock(return_value=AgentResponse(
            message="Lifecycle test response",
            confidence=0.9
        ))
        uow.ai_agent_repo.get_agent_status = AsyncMock(return_value={"status": "active"})
        uow.ai_agent_repo.shutdown_agent = AsyncMock(return_value=True)

        # Test lifecycle
        agent_id = await initialize_ai_agent(uow, config)
        assert agent_id == "lifecycle-agent-id"

        retrieved_config = await get_agent_configuration(uow, agent_id)
        assert retrieved_config == config

        response = await chat_with_agent(uow, agent_id, "Test message")
        assert response.message == "Lifecycle test response"

        status = await get_agent_status(uow, agent_id)
        assert status["status"] == "active"

        shutdown_result = await shutdown_agent(uow, agent_id)
        assert shutdown_result is True

        # Verify all methods were called
        uow.ai_agent_repo.initialize_agent.assert_called_once_with(config)
        uow.ai_agent_repo.get_agent_config.assert_called_once_with(agent_id)
        uow.ai_agent_repo.chat.assert_called_once_with(agent_id, "Test message", None, None)
        uow.ai_agent_repo.get_agent_status.assert_called_once_with(agent_id)
        uow.ai_agent_repo.shutdown_agent.assert_called_once_with(agent_id)