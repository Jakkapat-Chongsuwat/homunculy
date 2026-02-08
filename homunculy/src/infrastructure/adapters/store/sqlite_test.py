"""Tests for SQLiteStoreAdapter."""

import tempfile
from pathlib import Path

import pytest

from infrastructure.adapters.store import SQLiteStoreAdapter


@pytest.fixture
def store():
    """Create in-memory SQLite store."""
    store = SQLiteStoreAdapter(":memory:")
    yield store
    store.close()


@pytest.fixture
def file_store():
    """Create file-based SQLite store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        store = SQLiteStoreAdapter(str(db_path))
        yield store
        store.close()


@pytest.fixture
def sample_namespace():
    """Sample namespace for testing."""
    return ("user_1", "preferences")


@pytest.mark.asyncio
async def test_put_and_get_item(store, sample_namespace):
    """Test storing and retrieving item."""
    value = {"setting": "dark_mode", "enabled": True}

    store.put(sample_namespace, "theme", value)
    item = store.get(sample_namespace, "theme")

    assert item is not None
    assert item.namespace == sample_namespace
    assert item.key == "theme"
    assert item.value == value


@pytest.mark.asyncio
async def test_file_persistence(file_store, sample_namespace):
    """Test data persists to file."""
    value = {"data": "persisted"}
    file_store.put(sample_namespace, "test", value)

    item = file_store.get(sample_namespace, "test")
    assert item is not None
    assert item.value == value


@pytest.mark.asyncio
async def test_get_nonexistent_item(store, sample_namespace):
    """Test getting nonexistent item returns None."""
    item = store.get(sample_namespace, "missing")
    assert item is None


@pytest.mark.asyncio
async def test_search_in_namespace(store, sample_namespace):
    """Test searching items in namespace."""
    store.put(sample_namespace, "key1", {"data": "value1"})
    store.put(sample_namespace, "key2", {"data": "value2"})

    items = store.search(sample_namespace, limit=10)

    assert len(items) == 2
    keys = {i.key for i in items}
    assert keys == {"key1", "key2"}


@pytest.mark.asyncio
async def test_search_with_filter(store, sample_namespace):
    """Test searching with filter criteria."""
    store.put(sample_namespace, "k1", {"type": "A", "val": 1})
    store.put(sample_namespace, "k2", {"type": "B", "val": 2})

    items = store.search(sample_namespace, filter={"type": "A"}, limit=10)

    assert len(items) == 1
    assert items[0].key == "k1"


@pytest.mark.asyncio
async def test_search_with_limit(store, sample_namespace):
    """Test search respects limit."""
    for i in range(5):
        store.put(sample_namespace, f"key{i}", {"i": i})

    items = store.search(sample_namespace, limit=3)

    assert len(items) == 3


@pytest.mark.asyncio
async def test_delete_item(store, sample_namespace):
    """Test deleting an item."""
    store.put(sample_namespace, "test_key", {"data": "test"})

    store.delete(sample_namespace, "test_key")

    item = store.get(sample_namespace, "test_key")
    assert item is None


@pytest.mark.asyncio
async def test_delete_nonexistent_item(store, sample_namespace):
    """Test deleting nonexistent item is safe."""
    store.delete(sample_namespace, "missing")  # no error


@pytest.mark.asyncio
async def test_update_existing_item(store, sample_namespace):
    """Test updating existing item preserves created_at."""
    original = {"version": 1}
    updated = {"version": 2}

    store.put(sample_namespace, "config", original)
    first_item = store.get(sample_namespace, "config")

    store.put(sample_namespace, "config", updated)
    second_item = store.get(sample_namespace, "config")

    assert second_item.value == updated
    assert second_item.created_at == first_item.created_at
    assert second_item.updated_at >= first_item.updated_at


@pytest.mark.asyncio
async def test_multiple_namespaces_isolated(store):
    """Test namespaces are isolated from each other."""
    ns1 = ("user_1", "prefs")
    ns2 = ("user_2", "prefs")

    store.put(ns1, "key", {"user": "1"})
    store.put(ns2, "key", {"user": "2"})

    item1 = store.get(ns1, "key")
    item2 = store.get(ns2, "key")

    assert item1.value["user"] == "1"
    assert item2.value["user"] == "2"


@pytest.mark.asyncio
async def test_complex_namespace_serialization(store):
    """Test complex namespace tuple serialization."""
    ns = ("tenant_a", "user_123", "session_456", "preferences")

    store.put(ns, "key", {"data": "complex"})
    item = store.get(ns, "key")

    assert item is not None
    assert item.namespace == ns
    assert item.value == {"data": "complex"}


@pytest.mark.asyncio
async def test_pragmas_enabled(file_store):
    """Test WAL, synchronous=NORMAL are active on file-based store."""
    journal = file_store._conn.execute("PRAGMA journal_mode;").fetchone()
    sync = file_store._conn.execute("PRAGMA synchronous;").fetchone()
    assert journal[0] == "wal"
    assert sync[0] == 1  # NORMAL = 1


@pytest.mark.asyncio
async def test_context_manager():
    """Test context manager closes connection."""
    with SQLiteStoreAdapter(":memory:") as s:
        s.put(("ns",), "k", {"v": 1})
        assert s.get(("ns",), "k") is not None


@pytest.mark.asyncio
async def test_namespace_prefix_search(store):
    """Test search matches namespace prefixes."""
    store.put(("memories", "user_1"), "k1", {"data": "a"})
    store.put(("memories", "user_2"), "k2", {"data": "b"})
    store.put(("settings", "user_1"), "k3", {"data": "c"})

    results = store.search(("memories",), limit=10)
    assert len(results) == 2
    keys = {r.key for r in results}
    assert keys == {"k1", "k2"}
