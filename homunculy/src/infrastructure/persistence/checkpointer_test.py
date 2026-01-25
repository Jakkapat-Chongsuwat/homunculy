"""Tests for checkpointer module - Unit of Work pattern."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver

from infrastructure.persistence.checkpointer import (
    CheckpointerFactory,
    CheckpointerUnitOfWork,
    memory_checkpointer_context,
    postgres_checkpointer_context,
)


class TestCheckpointerUnitOfWork:
    """Tests for CheckpointerUnitOfWork."""

    def test_initial_state(self):
        """UoW starts uninitialized with no checkpointer."""
        uow = CheckpointerUnitOfWork()

        assert uow.checkpointer is None
        assert uow.storage_type == "none"
        assert uow.is_initialized is False

    def test_set_checkpointer(self):
        """Can set checkpointer via public method."""
        uow = CheckpointerUnitOfWork()
        mock = MagicMock()

        uow.set_checkpointer(mock)

        assert uow.checkpointer is mock

    def test_set_context(self):
        """Can set context via public method."""
        uow = CheckpointerUnitOfWork()
        mock = MagicMock()

        uow.set_context(mock)
        # Context is private but we verify via cleanup behavior

    @pytest.mark.asyncio
    async def test_setup_calls_checkpointer_setup(self):
        """Setup delegates to checkpointer.setup()."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.setup = AsyncMock()

        uow = CheckpointerUnitOfWork()
        uow.set_checkpointer(mock_checkpointer)

        await uow.setup()

        mock_checkpointer.setup.assert_called_once()
        assert uow.is_initialized is True

    @pytest.mark.asyncio
    async def test_setup_is_idempotent(self):
        """Setup only runs once."""
        mock_checkpointer = MagicMock()
        mock_checkpointer.setup = AsyncMock()

        uow = CheckpointerUnitOfWork()
        uow.set_checkpointer(mock_checkpointer)

        await uow.setup()
        await uow.setup()
        await uow.setup()

        mock_checkpointer.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_exits_context(self):
        """Cleanup exits the async context manager."""
        mock_context = MagicMock()
        mock_context.__aexit__ = AsyncMock()

        uow = CheckpointerUnitOfWork()
        uow.set_context(mock_context)
        uow.set_checkpointer(MagicMock())

        await uow.cleanup()

        mock_context.__aexit__.assert_called_once()
        assert uow.checkpointer is None
        assert uow.is_initialized is False

    def test_storage_type_returns_class_name(self):
        """Storage type returns checkpointer class name."""
        uow = CheckpointerUnitOfWork()
        uow.set_checkpointer(MagicMock())

        assert uow.storage_type == "MagicMock"


class TestCheckpointerFactory:
    """Tests for CheckpointerFactory."""

    @pytest.mark.asyncio
    async def test_create_postgres_success(self):
        """Factory creates PostgreSQL checkpointer."""
        mock_checkpointer = MagicMock()
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_checkpointer)

        mock_saver_class = MagicMock()
        mock_saver_class.from_conn_string.return_value = mock_context

        with patch(
            "langgraph.checkpoint.postgres.aio.AsyncPostgresSaver",
            mock_saver_class,
        ):
            uow = await CheckpointerFactory.create_postgres("postgresql://test")

            assert uow.checkpointer is mock_checkpointer
            mock_context.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_postgres_fallback_on_exception(self):
        """Factory falls back to MemorySaver on exception."""
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))

        mock_saver_class = MagicMock()
        mock_saver_class.from_conn_string.return_value = mock_context

        with patch(
            "langgraph.checkpoint.postgres.aio.AsyncPostgresSaver",
            mock_saver_class,
        ):
            uow = await CheckpointerFactory.create_postgres("postgresql://test")

            assert isinstance(uow.checkpointer, MemorySaver)

    def test_create_memory(self):
        """Factory creates MemorySaver."""
        uow = CheckpointerFactory.create_memory()

        assert isinstance(uow.checkpointer, MemorySaver)


class TestPostgresCheckpointerContext:
    """Tests for postgres_checkpointer_context."""

    @pytest.mark.asyncio
    async def test_context_yields_and_cleans_up(self):
        """Context manager yields UoW and cleans up."""
        mock_checkpointer = MagicMock()
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_checkpointer)
        mock_context.__aexit__ = AsyncMock()

        mock_saver_class = MagicMock()
        mock_saver_class.from_conn_string.return_value = mock_context

        with patch.dict(
            "os.environ",
            {"DB_HOST": "test", "DB_PORT": "5432", "DB_NAME": "test"},
        ):
            with patch(
                "langgraph.checkpoint.postgres.aio.AsyncPostgresSaver",
                mock_saver_class,
            ):
                async with postgres_checkpointer_context() as uow:
                    assert uow.checkpointer is mock_checkpointer

                # After exit, cleanup was called
                mock_context.__aexit__.assert_called()


class TestMemoryCheckpointerContext:
    """Tests for memory_checkpointer_context."""

    @pytest.mark.asyncio
    async def test_yields_memory_saver(self):
        """Memory context yields MemorySaver."""
        async with memory_checkpointer_context() as uow:
            assert isinstance(uow.checkpointer, MemorySaver)
            assert isinstance(uow, CheckpointerUnitOfWork)
