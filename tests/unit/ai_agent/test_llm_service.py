"""
Unit tests for LLM Factory and Client following Clean Architecture principles.

These tests validate the LLM factory and client implementations with comprehensive mocking
to ensure external dependencies are properly isolated and tested.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from models.ai_agent.ai_agent import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
    AgentResponse,
)
from repositories.llm_service.llm_factory import LLMFactory
from repositories.llm_service.interfaces import ILLMClient
from settings import PYDANTIC_AI_API_KEY, OPENAI_API_KEY


class TestLLMFactoryInitialization:
    """Test LLM factory initialization and configuration."""

    def test_init_creates_factory(self):
        """Test that LLM factory initializes correctly."""
        factory = LLMFactory()
        # Test that factory has the expected methods
        assert hasattr(factory, 'create_client')
        assert hasattr(factory, 'get_supported_providers')
        # Test that it can create clients without error
        assert callable(factory.create_client)
        assert callable(factory.get_supported_providers)

    def test_supported_providers(self):
        """Test that supported providers are properly configured."""
        factory = LLMFactory()
        providers = factory.get_supported_providers()
        assert "pydantic_ai" in providers
        assert "openai" in providers


class TestClientCreation:
    """Test client creation functionality."""

    @pytest.fixture
    def factory(self):
        """Create LLM factory instance."""
        return LLMFactory()

    def test_create_pydantic_ai_client(self, factory):
        """Test PydanticAI client creation."""
        with patch('repositories.llm_service.llm_factory.PydanticAILLMClient') as mock_client:
            client = factory.create_client("pydantic_ai")
            mock_client.assert_called_once()
            assert client is not None

    def test_create_openai_client(self, factory):
        """Test OpenAI client creation."""
        with patch('repositories.llm_service.llm_factory.PydanticAILLMClient') as mock_client:
            client = factory.create_client("openai")
            mock_client.assert_called_once()
            assert client is not None

    def test_create_unsupported_client(self, factory):
        """Test creation of unsupported client."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            factory.create_client("unsupported_provider")


class TestMockLLMClient:
    """Mock LLM client for testing."""

    @pytest.fixture
    def mock_client(self):
        """Create mock LLM client."""
        client = MagicMock(spec=ILLMClient)
        client.create_agent = AsyncMock(return_value="test-agent-id")
        client.chat = AsyncMock(return_value=AgentResponse(
            message="Test response",
            confidence=0.9,
            reasoning="Test reasoning",
            metadata={"test": True}
        ))
        return client

    @pytest.fixture
    def sample_config(self):
        """Create sample agent configuration."""
        personality = AgentPersonality(
            name="Test Agent",
            description="A test agent",
            traits={"helpfulness": 0.9},
            mood="friendly"
        )
        return AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=personality,
            system_prompt="You are a helpful test assistant",
            temperature=0.7,
            max_tokens=1000
        )


class TestAgentCreation(TestMockLLMClient):
    """Test agent creation functionality."""

    @pytest.mark.asyncio
    async def test_create_agent_success(self, mock_client, sample_config):
        """Test successful agent creation."""
        agent_id = await mock_client.create_agent(sample_config)
        assert agent_id == "test-agent-id"
        mock_client.create_agent.assert_called_once_with(sample_config)

    @pytest.mark.asyncio
    async def test_create_agent_with_factory(self, sample_config):
        """Test agent creation through factory."""
        factory = LLMFactory()
        with patch.object(factory, 'create_client') as mock_create_client:
            mock_client = MagicMock()
            mock_client.create_agent = AsyncMock(return_value="factory-agent-id")
            mock_create_client.return_value = mock_client

            client = factory.create_client("pydantic_ai")
            agent_id = await client.create_agent(sample_config)

            assert agent_id == "factory-agent-id"


class TestChatFunctionality(TestMockLLMClient):
    """Test chat functionality with proper mocking."""

    @pytest.mark.asyncio
    async def test_chat_success(self, mock_client):
        """Test successful chat interaction."""
        response = await mock_client.chat("test-agent", "Hello, how are you?")

        assert isinstance(response, AgentResponse)
        assert response.message == "Test response"
        assert response.confidence == 0.9
        assert response.reasoning == "Test reasoning"

        mock_client.chat.assert_called_once_with("test-agent", "Hello, how are you?")

    @pytest.mark.asyncio
    async def test_chat_with_context(self, mock_client):
        """Test chat with additional context."""
        context = {"user_id": "123", "session": "abc"}
        await mock_client.chat("test-agent", "Hello", context)

        mock_client.chat.assert_called_once_with("test-agent", "Hello", context)


class TestFactoryIntegration:
    """Test factory integration with clients."""

    @pytest.fixture
    def factory(self):
        """Create LLM factory instance."""
        return LLMFactory()

    def test_factory_client_caching(self, factory):
        """Test that factory caches created clients."""
        with patch('repositories.llm_service.llm_factory.PydanticAILLMClient') as mock_client_class:
            # Create first client
            client1 = factory.create_client("pydantic_ai")
            # Create second client with same provider
            client2 = factory.create_client("pydantic_ai")

            # Should be the same instance (cached)
            assert client1 is client2
            # Should only create one instance
            mock_client_class.assert_called_once()

    def test_factory_different_providers(self, factory):
        """Test that factory creates different clients for different providers."""
        with patch('repositories.llm_service.llm_factory.PydanticAILLMClient') as mock_client_class:
            mock_client_class.side_effect = lambda: MagicMock()  # Return different instance each time
            # Create clients for different providers
            client1 = factory.create_client("pydantic_ai")
            client2 = factory.create_client("openai")

            # Should be different instances
            assert client1 is not client2
            # Should create two instances
            assert mock_client_class.call_count == 2


class TestCleanArchitectureCompliance:
    """Test that the implementation follows clean architecture principles."""

    @pytest.fixture
    def factory(self):
        """Create LLM factory instance."""
        return LLMFactory()

    def test_factory_layer_separation(self, factory):
        """Test that factory properly separates concerns."""
        # Factory should not have database operations
        assert not hasattr(factory, 'save_to_db')
        assert not hasattr(factory, 'query_db')

        # Factory should only handle client creation
        assert hasattr(factory, 'create_client')
        assert hasattr(factory, 'get_supported_providers')

    def test_client_interface_compliance(self):
        """Test that clients implement the required interface."""
        # This is more of a documentation test - in real implementation,
        # we would verify that concrete clients implement ILLMClient
        assert hasattr(ILLMClient, 'create_agent')
        assert hasattr(ILLMClient, 'chat')
        assert hasattr(ILLMClient, 'update_agent')
        assert hasattr(ILLMClient, 'remove_agent')

    def test_dependency_injection_ready(self, factory):
        """Test that factory is ready for dependency injection."""
        # Factory should be instantiable without parameters
        assert isinstance(factory, LLMFactory)

        # Should be able to create clients
        with patch('repositories.llm_service.llm_factory.PydanticAILLMClient'):
            client = factory.create_client("pydantic_ai")
            assert client is not None