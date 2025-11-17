"""
Unit tests for AI agent use cases following Clean Architecture principles.

These tests validate the AI agent use cases with comprehensive mocking
to ensure proper separation of concerns and external dependency isolation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Dict, Any

from models.ai_agent.ai_agent import (
    AgentProvider,
    AgentStatus,
    AgentPersonality,
    AgentConfiguration,
    AgentResponse
)
from repositories.llm_service.llm_factory import LLMFactory
from usecases.ai_agent import (
    create_llm_agent,
    chat_with_llm_agent,
    update_llm_agent,
    remove_llm_agent,
    get_supported_llm_providers
)


class TestCreateLLMAgent:
    """Test cases for create_llm_agent use case."""

    @pytest.fixture
    def mock_llm_factory(self):
        """Create a mock LLM factory."""
        factory = MagicMock(spec=LLMFactory)
        mock_client = AsyncMock()
        factory.create_client.return_value = mock_client
        return factory

    @pytest.fixture
    def agent_config(self):
        """Create a test agent configuration."""
        return AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(
                name="Test Agent",
                description="A test AI agent",
                traits={"helpfulness": 0.9, "friendliness": 0.8},
                mood="neutral",
                memory_context="Test context"
            ),
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
            max_tokens=1000
        )

    @pytest.mark.asyncio
    async def test_create_llm_agent_success(self, mock_llm_factory, agent_config):
        """Test successful LLM agent creation."""
        # Arrange
        agent_id = "test-agent-123"

        # Act
        await create_llm_agent(mock_llm_factory, agent_id, agent_config)

        # Assert
        mock_llm_factory.create_client.assert_called_once_with("pydantic_ai")
        mock_llm_factory.create_client.return_value.create_agent.assert_called_once_with(agent_config)

    @pytest.mark.asyncio
    async def test_create_llm_agent_with_provider_value(self, mock_llm_factory, agent_config):
        """Test agent creation with provider having value attribute."""
        # Arrange
        agent_id = "test-agent-123"
        agent_config.provider = MagicMock()
        agent_config.provider.value = "custom_provider"

        # Act
        await create_llm_agent(mock_llm_factory, agent_id, agent_config)

        # Assert
        mock_llm_factory.create_client.assert_called_once_with("custom_provider")

    @pytest.mark.asyncio
    async def test_create_llm_agent_failure(self, mock_llm_factory, agent_config):
        """Test LLM agent creation failure."""
        # Arrange
        agent_id = "test-agent-123"
        mock_llm_factory.create_client.return_value.create_agent.side_effect = Exception("Creation failed")

        # Act & Assert
        with pytest.raises(Exception, match="Creation failed"):
            await create_llm_agent(mock_llm_factory, agent_id, agent_config)


class TestChatWithLLMAgent:
    """Test cases for chat_with_llm_agent use case."""

    @pytest.fixture
    def mock_llm_factory(self):
        """Create a mock LLM factory."""
        factory = MagicMock(spec=LLMFactory)
        mock_client = AsyncMock()
        mock_response = AgentResponse(
            message="Hello! How can I help you?",
            confidence=0.9,
            reasoning="This is a test response",
            metadata={"test": True}
        )
        mock_client.chat.return_value = mock_response
        factory.create_client.return_value = mock_client
        return factory

    @pytest.mark.asyncio
    async def test_chat_with_llm_agent_success(self, mock_llm_factory):
        """Test successful chat with LLM agent."""
        # Arrange
        agent_id = "test-agent-123"
        message = "Hello, how are you?"
        context = {"user_id": "user-456"}

        # Act
        response = await chat_with_llm_agent(mock_llm_factory, agent_id, message, context)

        # Assert
        mock_llm_factory.create_client.assert_called_once_with("pydantic_ai")
        mock_llm_factory.create_client.return_value.chat.assert_called_once_with(agent_id, message, context)
        assert response.message == "Hello! How can I help you?"
        assert response.confidence == 0.9

    @pytest.mark.asyncio
    async def test_chat_with_llm_agent_no_context(self, mock_llm_factory):
        """Test chat without context."""
        # Arrange
        agent_id = "test-agent-123"
        message = "Hello!"

        # Act
        response = await chat_with_llm_agent(mock_llm_factory, agent_id, message)

        # Assert
        mock_llm_factory.create_client.return_value.chat.assert_called_once_with(agent_id, message, None)


class TestUpdateLLMAgent:
    """Test cases for update_llm_agent use case."""

    @pytest.fixture
    def mock_llm_factory(self):
        """Create a mock LLM factory."""
        factory = MagicMock(spec=LLMFactory)
        mock_client = AsyncMock()
        factory.create_client.return_value = mock_client
        return factory

    @pytest.fixture
    def agent_config(self):
        """Create a test agent configuration."""
        return AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=AgentPersonality(
                name="Updated Agent",
                description="An updated AI agent",
                traits={"creativity": 0.9, "helpfulness": 0.8, "smartness": 0.7},
                mood="happy",
                memory_context="Updated context"
            ),
            system_prompt="You are a very helpful assistant.",
            temperature=0.8,
            max_tokens=1500
        )

    @pytest.mark.asyncio
    async def test_update_llm_agent_success(self, mock_llm_factory, agent_config):
        """Test successful LLM agent update."""
        # Arrange
        agent_id = "test-agent-123"

        # Act
        await update_llm_agent(mock_llm_factory, agent_id, agent_config)

        # Assert
        mock_llm_factory.create_client.assert_called_once_with("pydantic_ai")
        mock_llm_factory.create_client.return_value.update_agent.assert_called_once_with(agent_id, agent_config)


class TestRemoveLLMAgent:
    """Test cases for remove_llm_agent use case."""

    @pytest.fixture
    def mock_llm_factory(self):
        """Create a mock LLM factory."""
        factory = MagicMock(spec=LLMFactory)
        mock_client = AsyncMock()
        factory.create_client.return_value = mock_client
        return factory

    @pytest.mark.asyncio
    async def test_remove_llm_agent_success_first_provider(self, mock_llm_factory):
        """Test successful agent removal on first provider."""
        # Arrange
        agent_id = "test-agent-123"

        # Act
        await remove_llm_agent(mock_llm_factory, agent_id)

        # Assert
        # Should try pydantic_ai first
        assert mock_llm_factory.create_client.call_count == 1
        mock_llm_factory.create_client.assert_called_with("pydantic_ai")
        mock_llm_factory.create_client.return_value.remove_agent.assert_called_once_with(agent_id)

    @pytest.mark.asyncio
    async def test_remove_llm_agent_success_second_provider(self, mock_llm_factory):
        """Test successful agent removal on second provider after first fails."""
        # Arrange
        agent_id = "test-agent-123"
        mock_llm_factory.create_client.return_value.remove_agent.side_effect = [Exception("Not found"), None]

        # Act
        await remove_llm_agent(mock_llm_factory, agent_id)

        # Assert
        # Should try both providers
        assert mock_llm_factory.create_client.call_count == 2
        mock_llm_factory.create_client.assert_any_call("pydantic_ai")
        mock_llm_factory.create_client.assert_any_call("openai")

    @pytest.mark.asyncio
    async def test_remove_llm_agent_all_fail(self, mock_llm_factory):
        """Test agent removal when all providers fail (should not raise error)."""
        # Arrange
        agent_id = "test-agent-123"
        mock_llm_factory.create_client.return_value.remove_agent.side_effect = Exception("Not found")

        # Act & Assert
        # Should not raise any error
        await remove_llm_agent(mock_llm_factory, agent_id)


class TestGetSupportedLLMProviders:
    """Test cases for get_supported_llm_providers use case."""

    @pytest.fixture
    def mock_llm_factory(self):
        """Create a mock LLM factory."""
        factory = MagicMock(spec=LLMFactory)
        factory.get_supported_providers.return_value = ["pydantic_ai", "openai", "anthropic"]
        return factory

    def test_get_supported_llm_providers(self, mock_llm_factory):
        """Test getting supported LLM providers."""
        # Act
        providers = get_supported_llm_providers(mock_llm_factory)

        # Assert
        mock_llm_factory.get_supported_providers.assert_called_once()
        assert providers == ["pydantic_ai", "openai", "anthropic"]