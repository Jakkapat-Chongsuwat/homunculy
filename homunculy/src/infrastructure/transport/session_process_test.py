"""Unit tests for session process runner."""

from unittest.mock import AsyncMock, patch

import pytest

from infrastructure.transport import session_process


def test_value_prefers_argument() -> None:
    assert session_process.resolve_value("arg", "MISSING") == "arg"


def test_value_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVEKIT_URL", "ws://example")
    assert session_process.resolve_value(None, "LIVEKIT_URL") == "ws://example"


def test_value_raises_when_missing() -> None:
    with pytest.raises(SystemExit):
        session_process.resolve_value(None, "MISSING_ENV")


def test_conn_string_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "homunculy")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    assert session_process.connection_string() == "postgresql://user:pass@db:5433/homunculy"


@pytest.mark.asyncio
async def test_run_session_cleans_up() -> None:
    uow = AsyncMock()
    with patch.object(session_process, "_create_checkpointer", AsyncMock(return_value=uow)):
        with patch.object(session_process, "_start_pipeline", AsyncMock()):
            await session_process.run_session("u", "t", "r", "s")

    uow.cleanup.assert_awaited_once()
