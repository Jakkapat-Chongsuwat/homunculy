"""
Unit tests for CheckpointerManager.

Tests checkpoint lifecycle management.
"""

from unittest.mock import MagicMock, patch

import pytest

from internal.infrastructure.services.langgraph.checkpointer import (
    CheckpointerManager,
    create_checkpointer_manager,
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
            "_should_use_postgres",
            return_value=False,
        ):
            manager = CheckpointerManager()
            await manager.ensure_initialized()

            assert manager.is_initialized
            assert manager.storage_type == "memory"


class TestCheckpointerManagerFactory:
    """Test factory function for CheckpointerManager."""

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
