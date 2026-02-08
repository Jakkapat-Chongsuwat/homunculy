"""Tests for MemoryService."""

import pytest

from application.services import MemoryService
from infrastructure.adapters.store import InMemoryStoreAdapter


@pytest.fixture
def store():
    """Create store instance."""
    return InMemoryStoreAdapter()


@pytest.fixture
def service(store):
    """Create memory service."""
    return MemoryService(store)


@pytest.fixture
def test_namespace():
    """Test namespace."""
    return ("companion", "user_1")


@pytest.mark.asyncio
async def test_get_memory_returns_default(service, test_namespace):
    """Test get_memory initializes with default."""
    default_content = "Default preference text"

    result = await service.get_memory(
        test_namespace,
        "preferences",
        default_content,
    )

    assert result == default_content


@pytest.mark.asyncio
async def test_get_memory_returns_existing(service, test_namespace):
    """Test get_memory returns existing value."""
    content = "Stored preference"

    await service.update_memory(test_namespace, "preferences", content)
    result = await service.get_memory(test_namespace, "preferences")

    assert result == content


@pytest.mark.asyncio
async def test_update_memory_stores_content(service, test_namespace):
    """Test update_memory stores new content."""
    content = "Updated preferences"

    await service.update_memory(test_namespace, "preferences", content)
    result = await service.get_memory(test_namespace, "preferences")

    assert result == content


@pytest.mark.asyncio
async def test_search_memories_returns_all(service, test_namespace):
    """Test search_memories returns all items."""
    await service.update_memory(test_namespace, "key1", "content1")
    await service.update_memory(test_namespace, "key2", "content2")

    results = await service.search_memories(test_namespace, limit=10)

    assert len(results) == 2
    assert "content1" in results
    assert "content2" in results


@pytest.mark.asyncio
async def test_search_memories_respects_limit(service, test_namespace):
    """Test search_memories respects limit."""
    for i in range(5):
        await service.update_memory(test_namespace, f"key{i}", f"c{i}")

    results = await service.search_memories(test_namespace, limit=3)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_get_memory_without_default_returns_none(
    service,
    test_namespace,
):
    """Test get_memory without default returns None."""
    result = await service.get_memory(test_namespace, "missing")
    assert result is None


@pytest.mark.asyncio
async def test_memory_isolation_across_namespaces(service):
    """Test memories are isolated across namespaces."""
    ns1 = ("companion", "user_1")
    ns2 = ("companion", "user_2")

    await service.update_memory(ns1, "pref", "user1_data")
    await service.update_memory(ns2, "pref", "user2_data")

    result1 = await service.get_memory(ns1, "pref")
    result2 = await service.get_memory(ns2, "pref")

    assert result1 == "user1_data"
    assert result2 == "user2_data"
