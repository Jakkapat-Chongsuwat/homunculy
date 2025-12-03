"""
Unit tests for ThreadResolver.

Tests thread ID resolution from context.
"""

import pytest

from internal.domain.entities import (
    AgentConfiguration,
    AgentPersonality,
    AgentProvider,
)
from internal.infrastructure.services.langgraph.graph import ThreadResolver


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
