"""Unit tests for AI Agent domain models."""

import pytest
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Any

from pydantic import ValidationError

from src.models.ai_agent import (
    AgentProvider,
    AgentStatus,
    AgentPersonality,
    AgentConfiguration,
    AgentThread,
    AgentMessage,
    AgentResponse,
    AgentException,
    AgentInitializationError,
    AgentExecutionError,
    AgentConfigurationError,
)


class TestAgentProvider:
    """Test AgentProvider enum."""
    
    def test_agent_provider_values(self):
        """Test AgentProvider enum values."""
        assert AgentProvider.PYDANTIC_AI.value == "pydantic_ai"
        assert AgentProvider.OPENAI.value == "openai"
        assert AgentProvider.LANGRAPH.value == "langraph"
        assert AgentProvider.AUTOGEN.value == "autogen"


class TestAgentStatus:
    """Test AgentStatus enum."""
    
    def test_agent_status_values(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.THINKING.value == "thinking"
        assert AgentStatus.RESPONDING.value == "responding"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.COMPLETED.value == "completed"


class TestAgentMessage:
    """Test AgentMessage dataclass."""
    
    def test_create_agent_message(self):
        """Test creating AgentMessage."""
        timestamp = datetime.now(timezone.utc)
        message = AgentMessage(
            role="user",
            content="Hello, assistant!",
            timestamp=timestamp
        )
        
        assert message.role == "user"
        assert message.content == "Hello, assistant!"
        assert message.timestamp == timestamp
        assert message.metadata is None
    
    def test_agent_message_with_metadata(self):
        """Test AgentMessage with metadata."""
        timestamp = datetime.now(timezone.utc)
        metadata = {"source": "test", "priority": "high"}
        message = AgentMessage(
            role="assistant",
            content="Hello, user!",
            timestamp=timestamp,
            metadata=metadata
        )
        
        assert message.metadata == metadata
        assert message.metadata is not None
        assert message.metadata["source"] == "test"
    
    def test_agent_message_serialization(self):
        """Test AgentMessage serialization via asdict."""
        timestamp = datetime.now(timezone.utc)
        message = AgentMessage(
            role="system",
            content="System message",
            timestamp=timestamp,
            metadata={"type": "system"}
        )
        
        data = asdict(message)
        assert data["role"] == "system"
        assert data["content"] == "System message"
        assert data["timestamp"] == timestamp
        assert data["metadata"]["type"] == "system"


class TestAgentResponse:
    """Test AgentResponse dataclass."""
    
    def test_create_agent_response_minimal(self):
        """Test creating AgentResponse with minimal fields."""
        response = AgentResponse(
            message="Hello, user!",
            confidence=0.95
        )
        
        assert response.message == "Hello, user!"
        assert response.confidence == 0.95
        assert response.reasoning is None
        assert response.metadata is None
        assert response.status == AgentStatus.COMPLETED
    
    def test_create_agent_response_full(self):
        """Test creating AgentResponse with all fields."""
        metadata = {"model": "gpt-4", "tokens": 150}
        response = AgentResponse(
            message="Detailed response",
            confidence=0.87,
            reasoning="Based on training data analysis",
            metadata=metadata,
            status=AgentStatus.THINKING
        )
        
        assert response.message == "Detailed response"
        assert response.confidence == 0.87
        assert response.reasoning == "Based on training data analysis"
        assert response.metadata == metadata
        assert response.status == AgentStatus.THINKING
    
    def test_agent_response_serialization(self):
        """Test AgentResponse serialization via asdict."""
        response = AgentResponse(
            message="Test response",
            confidence=0.9,
            metadata={"test": True}
        )
        
        data = asdict(response)
        assert data["message"] == "Test response"
        assert data["confidence"] == 0.9
        assert data["status"] == AgentStatus.COMPLETED
        assert data["metadata"]["test"] is True


class TestAgentPersonality:
    """Test AgentPersonality Pydantic model."""
    
    def test_create_personality_minimal(self):
        """Test creating AgentPersonality with minimal fields."""
        personality = AgentPersonality(
            name="Test Assistant",
            description="A helpful test assistant"
        )
        
        assert personality.name == "Test Assistant"
        assert personality.description == "A helpful test assistant"
        assert personality.traits == {}
        assert personality.mood == "neutral"
        assert personality.memory_context == ""
    
    def test_create_personality_with_traits(self):
        """Test creating AgentPersonality with traits."""
        traits = {"humor": 0.8, "formality": 0.3}
        personality = AgentPersonality(
            name="Funny Assistant",
            description="A humorous assistant",
            traits=traits,
            mood="cheerful",
            memory_context="Previous conversation about jokes"
        )
        
        assert personality.traits == traits
        assert personality.mood == "cheerful"
        assert personality.memory_context == "Previous conversation about jokes"
    
    def test_personality_validation(self):
        """Test AgentPersonality validation."""
        # Test that empty strings are allowed (Pydantic v2 behavior)
        personality = AgentPersonality(name="", description="Empty name")
        assert personality.name == ""
        assert personality.description == "Empty name"
    
    def test_personality_serialization(self):
        """Test AgentPersonality serialization."""
        personality = AgentPersonality(
            name="Serializable",
            description="Test serialization",
            traits={"creativity": 0.9}
        )
        
        data = personality.model_dump()
        assert data["name"] == "Serializable"
        assert data["traits"]["creativity"] == 0.9


class TestAgentConfiguration:
    """Test AgentConfiguration Pydantic model."""
    
    def test_create_configuration_minimal(self):
        """Test creating AgentConfiguration with minimal fields."""
        personality = AgentPersonality(name="Test", description="Test personality")
        config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=personality
        )
        
        assert config.provider == AgentProvider.PYDANTIC_AI
        assert config.model_name == "gpt-4"
        assert config.personality == personality
        assert config.system_prompt == ""
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.tools == []
    
    def test_create_configuration_full(self):
        """Test creating AgentConfiguration with all fields."""
        personality = AgentPersonality(name="Full Test", description="Full test personality")
        tools = ["web_search", "calculator"]
        config = AgentConfiguration(
            provider=AgentProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            personality=personality,
            system_prompt="You are a helpful assistant",
            temperature=0.5,
            max_tokens=1000,
            tools=tools
        )
        
        assert config.provider == AgentProvider.OPENAI
        assert config.model_name == "gpt-3.5-turbo"
        assert config.system_prompt == "You are a helpful assistant"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.tools == tools
    
    def test_configuration_validation(self):
        """Test AgentConfiguration validation."""
        personality = AgentPersonality(name="Test", description="Test")
        
        # Test temperature validation
        with pytest.raises(ValidationError):
            AgentConfiguration(
                provider=AgentProvider.PYDANTIC_AI,
                model_name="gpt-4",
                personality=personality,
                temperature=3.0  # Invalid: > 2.0
            )
        
        # Test max_tokens validation
        with pytest.raises(ValidationError):
            AgentConfiguration(
                provider=AgentProvider.PYDANTIC_AI,
                model_name="gpt-4",
                personality=personality,
                max_tokens=0  # Invalid: must be > 0
            )


class TestAgentThread:
    """Test AgentThread Pydantic model."""
    
    def test_create_thread_minimal(self):
        """Test creating AgentThread with minimal fields."""
        thread = AgentThread(
            id="thread-123",
            agent_id="agent-456"
        )
        
        assert thread.id == "thread-123"
        assert thread.agent_id == "agent-456"
        assert thread.messages == []
        assert isinstance(thread.created_at, datetime)
        assert isinstance(thread.updated_at, datetime)
        assert thread.metadata == {}
    
    def test_create_thread_with_messages(self):
        """Test creating AgentThread with messages."""
        timestamp = datetime.now(timezone.utc)
        messages = [
            AgentMessage(role="user", content="Hello", timestamp=timestamp),
            AgentMessage(role="assistant", content="Hi there!", timestamp=timestamp)
        ]
        metadata = {"session_id": "sess-789"}
        
        thread = AgentThread(
            id="thread-456",
            agent_id="agent-789",
            messages=messages,
            metadata=metadata
        )
        
        assert len(thread.messages) == 2
        assert thread.messages[0].role == "user"
        assert thread.messages[1].role == "assistant"
        assert thread.metadata == metadata
    
    def test_thread_serialization(self):
        """Test AgentThread serialization."""
        timestamp = datetime.now(timezone.utc)
        message = AgentMessage(role="user", content="Test", timestamp=timestamp)
        thread = AgentThread(
            id="thread-serialize",
            agent_id="agent-serialize",
            messages=[message]
        )
        
        data = thread.model_dump()
        assert data["id"] == "thread-serialize"
        assert data["agent_id"] == "agent-serialize"
        assert len(data["messages"]) == 1


class TestAgentExceptions:
    """Test AI agent exception classes."""
    
    def test_agent_exception(self):
        """Test base AgentException."""
        with pytest.raises(AgentException) as exc_info:
            raise AgentException("Base agent error")
        
        assert str(exc_info.value) == "Base agent error"
        assert isinstance(exc_info.value, Exception)
    
    def test_agent_initialization_error(self):
        """Test AgentInitializationError."""
        with pytest.raises(AgentInitializationError) as exc_info:
            raise AgentInitializationError("Failed to initialize agent")
        
        assert str(exc_info.value) == "Failed to initialize agent"
        assert isinstance(exc_info.value, AgentException)
    
    def test_agent_execution_error(self):
        """Test AgentExecutionError."""
        with pytest.raises(AgentExecutionError) as exc_info:
            raise AgentExecutionError("Agent execution failed")
        
        assert str(exc_info.value) == "Agent execution failed"
        assert isinstance(exc_info.value, AgentException)
    
    def test_agent_configuration_error(self):
        """Test AgentConfigurationError."""
        with pytest.raises(AgentConfigurationError) as exc_info:
            raise AgentConfigurationError("Invalid configuration")
        
        assert str(exc_info.value) == "Invalid configuration"
        assert isinstance(exc_info.value, AgentException)


class TestModelIntegration:
    """Test integration between different models."""
    
    def test_complete_agent_setup(self):
        """Test complete agent setup with all components."""
        # Create personality
        personality = AgentPersonality(
            name="Integration Test Assistant",
            description="Assistant for testing integration",
            traits={"helpfulness": 0.9, "patience": 0.8},
            mood="focused"
        )
        
        # Create configuration
        config = AgentConfiguration(
            provider=AgentProvider.PYDANTIC_AI,
            model_name="gpt-4",
            personality=personality,
            system_prompt="You are a helpful integration test assistant",
            temperature=0.6,
            tools=["search", "calculate"]
        )
        
        # Create thread with messages
        timestamp = datetime.now(timezone.utc)
        messages = [
            AgentMessage(role="user", content="Start integration test", timestamp=timestamp),
            AgentMessage(role="assistant", content="Integration test started", timestamp=timestamp)
        ]
        
        thread = AgentThread(
            id="integration-thread",
            agent_id="integration-agent",
            messages=messages,
            metadata={"test_type": "integration"}
        )
        
        # Create response
        response = AgentResponse(
            message="Integration test completed successfully",
            confidence=0.95,
            reasoning="All components worked together properly",
            metadata={"integration_test": True},
            status=AgentStatus.COMPLETED
        )
        
        # Verify relationships and data integrity
        assert config.personality.name == "Integration Test Assistant"
        assert len(thread.messages) == 2
        assert thread.messages[0].content == "Start integration test"
        assert response.status == AgentStatus.COMPLETED
        assert response.metadata is not None
        assert response.metadata["integration_test"] is True
        
        # Test serialization compatibility
        config_data = config.model_dump()
        thread_data = thread.model_dump()
        response_data = asdict(response)

        assert config_data["provider"] == AgentProvider.PYDANTIC_AI
        assert len(thread_data["messages"]) == 2
        assert response_data["confidence"] == 0.95