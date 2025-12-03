"""
Unit tests for modular LangGraph components.

Tests CheckpointerManager, GraphManager, ResponseBuilder.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from internal.domain.entities import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
    AgentStatus,
)
from internal.infrastructure.services.langgraph.checkpointer_manager import (
    CheckpointerManager,
    create_checkpointer_manager,
)
from internal.infrastructure.services.langgraph.graph_manager import (
    GraphManager,
    ThreadResolver,
)
from internal.infrastructure.services.langgraph.response_builder import (
    ResponseBuilder,
    create_response_builder,
)


class TestCheckpointerManager:
    """Test CheckpointerManager functionality."""

    def test_init_with_checkpointer(self):
        """Should accept pre-configured checkpointer."""
        mock_checkpointer = MagicMock()
        manager = CheckpointerManager(checkpointer=mock_checkpointer)

        assert manager.checkpointer == mock_checkpointer
        assert manager.is_initialized

    def test_init_without_checkpointer(self):
        """Should initialize as not ready."""
        manager = CheckpointerManager()

        assert manager.checkpointer is None
        assert not manager.is_initialized

    def test_storage_type_none(self):
        """Storage type should be 'none' when not initialized."""
        manager = CheckpointerManager()
        assert manager.storage_type == "none"

    def test_storage_type_memory(self):
        """Should detect memory saver."""
        mock = MagicMock()
        mock.__class__.__name__ = "MemorySaver"
        manager = CheckpointerManager(checkpointer=mock)

        assert manager.storage_type == "memory"

    @pytest.mark.asyncio
    async def test_ensure_initialized_already_done(self):
        """Should skip if already initialized."""
        mock = MagicMock()
        manager = CheckpointerManager(checkpointer=mock)

        await manager.ensure_initialized()
        # Should not raise or change state
        assert manager.is_initialized

    @pytest.mark.asyncio
    async def test_ensure_initialized_uses_memory_fallback(self):
        """Should fall back to MemorySaver when Postgres unavailable."""
        with patch.object(
            CheckpointerManager,
            '_should_use_postgres',
            return_value=False,
        ):
            manager = CheckpointerManager()
            await manager.ensure_initialized()

            assert manager.is_initialized
            assert manager.storage_type == "memory"


class TestThreadResolver:
    """Test ThreadResolver functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AgentConfiguration(
            provider=AgentProvider.LANGRAPH,
            model_name="gpt-4o-mini",
            personality=AgentPersonality(
                name="Test",
                description="Test agent",
                mood="neutral",
            ),
        )

    def test_resolve_no_context(self, config):
        """Should return 'default' when no context."""
        result = ThreadResolver.resolve(config, None)
        assert result == "default"

    def test_resolve_empty_context(self, config):
        """Should return 'default' for empty context."""
        result = ThreadResolver.resolve(config, {})
        assert result == "default"

    def test_resolve_with_session_id(self, config):
        """Session ID should take priority."""
        context = {"session_id": "abc123", "user_id": "user1"}
        result = ThreadResolver.resolve(config, context)

        assert result == "session:abc123"

    def test_resolve_with_user_id(self, config):
        """Should use user_id:model_name format."""
        context = {"user_id": "user1"}
        result = ThreadResolver.resolve(config, context)

        assert result == "user:user1:gpt-4o-mini"

    def test_resolve_with_user_and_agent_id(self, config):
        """Should use agent_id when provided."""
        context = {"user_id": "user1", "agent_id": "custom-agent"}
        result = ThreadResolver.resolve(config, context)

        assert result == "user:user1:custom-agent"


class TestResponseBuilder:
    """Test ResponseBuilder functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AgentConfiguration(
            provider=AgentProvider.LANGRAPH,
            model_name="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
            personality=AgentPersonality(
                name="Test",
                description="Test agent",
                mood="happy",
            ),
        )

    def test_build_success(self, config):
        """Should build successful response."""
        builder = ResponseBuilder(storage_type="postgres")

        response = builder.build_success(
            configuration=config,
            thread_id="test-thread",
            response_text="Hello!",
            summary_used=True,
            checkpointer_name="AsyncPostgresSaver",
        )

        assert response.message == "Hello!"
        assert response.status == AgentStatus.COMPLETED
        assert response.confidence == 0.95
        assert response.metadata is not None
        assert response.metadata["thread_id"] == "test-thread"
        assert response.metadata["summary_used"] is True
        assert response.metadata["storage_type"] == "postgres"

    def test_build_success_with_audio(self, config):
        """Should include audio in metadata."""
        builder = ResponseBuilder()

        audio = {"data": "base64data", "format": "mp3"}
        response = builder.build_success(
            configuration=config,
            thread_id="test",
            response_text="Hi",
            summary_used=False,
            checkpointer_name="MemorySaver",
            audio_response=audio,
        )

        assert response.metadata is not None
        assert response.metadata["audio"] == audio

    def test_build_error(self):
        """Should build error response."""
        builder = ResponseBuilder()

        response = builder.build_error("Something went wrong")

        assert "Error:" in response.message
        assert response.status == AgentStatus.ERROR
        assert response.confidence == 0.0
        assert response.metadata is not None
        assert response.metadata["error"] == "Something went wrong"

    @pytest.mark.asyncio
    async def test_generate_audio_no_service(self):
        """Should return None when no TTS service."""
        builder = ResponseBuilder(tts_service=None)

        result = await builder.generate_audio("Hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_audio_short_text(self):
        """Should skip very short text."""
        mock_tts = MagicMock()
        builder = ResponseBuilder(tts_service=mock_tts)

        result = await builder.generate_audio("Hi")
        assert result is None


class TestGraphManager:
    """Test GraphManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AgentConfiguration(
            provider=AgentProvider.LANGRAPH,
            model_name="gpt-4o-mini",
            temperature=0.5,
            max_tokens=500,
            personality=AgentPersonality(
                name="Test",
                description="Test",
                mood="neutral",
            ),
        )

    def test_clear_cache(self):
        """Should clear cached graphs without error."""
        manager = GraphManager(
            api_key="test-key",
            checkpointer=MagicMock(),
        )
        manager.clear_cache()
        # Should not raise

    def test_update_checkpointer(self):
        """Updating checkpointer should work."""
        manager = GraphManager(
            api_key="test-key",
            checkpointer=MagicMock(),
        )
        new_checkpointer = MagicMock()
        manager.update_checkpointer(new_checkpointer)
        # Should not raise


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_checkpointer_manager(self):
        """Factory should create manager."""
        manager = create_checkpointer_manager()
        assert isinstance(manager, CheckpointerManager)

    def test_create_checkpointer_manager_with_checkpointer(self):
        """Factory should accept checkpointer."""
        mock = MagicMock()
        manager = create_checkpointer_manager(checkpointer=mock)

        assert manager.checkpointer == mock
        assert manager.is_initialized

    def test_create_response_builder(self):
        """Factory should create builder."""
        builder = create_response_builder()
        assert isinstance(builder, ResponseBuilder)

    def test_create_response_builder_with_options(self):
        """Factory should accept options."""
        mock_tts = MagicMock()
        builder = create_response_builder(
            tts_service=mock_tts,
            storage_type="postgres",
        )
        # Verify it was created successfully
        assert isinstance(builder, ResponseBuilder)
