"""Unit tests for session stores."""

import pytest

from domain.interfaces import ChannelInbound
from infrastructure.persistence.redislite_session_store import RedisliteSessionStore
from infrastructure.persistence.session_store import InMemorySessionStore
from infrastructure.persistence.sqlite_session_store import SQLiteSessionStore


def _inbound(user_id: str) -> ChannelInbound:
    return ChannelInbound("t1", "line", user_id, "hello", {})


def test_get_or_create_is_stable() -> None:
    store = InMemorySessionStore()
    first = store.get_or_create(_inbound("u1"))
    second = store.get_or_create(_inbound("u1"))

    assert first.id == second.id


def test_different_users_get_different_sessions() -> None:
    store = InMemorySessionStore()
    first = store.get_or_create(_inbound("u1"))
    second = store.get_or_create(_inbound("u2"))

    assert first.id != second.id


def test_redislite_store_round_trip(tmp_path) -> None:
    db_file = tmp_path / "redis.db"
    try:
        store = RedisliteSessionStore(str(db_file))
    except RuntimeError:
        pytest.skip("redislite unavailable on this platform")
    first = store.get_or_create(_inbound("u1"))
    second = store.get_or_create(_inbound("u1"))

    assert first.id == second.id


def test_sqlite_store_round_trip(tmp_path) -> None:
    db_file = tmp_path / "sessions.db"
    store = SQLiteSessionStore(str(db_file))
    first = store.get_or_create(_inbound("u1"))
    second = store.get_or_create(_inbound("u1"))

    assert first.id == second.id
