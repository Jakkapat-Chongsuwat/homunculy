"""
Unit tests for GraphManager.

Tests graph caching and building.
"""

from unittest.mock import MagicMock

import pytest

from internal.domain.entities import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
)
from internal.infrastructure.services.langgraph.graph import (
    GraphManager,
    create_graph_manager,
)


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


class TestGraphManagerFactory:
    """Test factory functions for GraphManager."""

    def test_create_graph_manager(self):
        """Factory should create manager with required args."""
        manager = create_graph_manager(
            api_key="test-key",
            checkpointer=MagicMock(),
        )
        assert isinstance(manager, GraphManager)

    def test_create_graph_manager_with_services(self):
        """Factory should accept optional services."""
        manager = create_graph_manager(
            api_key="test-key",
            checkpointer=MagicMock(),
            tts_service=MagicMock(),
            rag_service=MagicMock(),
        )
        assert isinstance(manager, GraphManager)
