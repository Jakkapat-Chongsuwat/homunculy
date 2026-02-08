"""E2E tests for LangGraph memory system integration."""

import tempfile
from pathlib import Path

import pytest

from application.services import MemoryService
from infrastructure.adapters.store import InMemoryStoreAdapter, SQLiteStoreAdapter


@pytest.fixture(params=["inmemory", "sqlite"])
def memory_system(request):
    """Create complete memory system for e2e testing.

    Tests both InMemory and SQLite adapters.
    """
    if request.param == "inmemory":
        store = InMemoryStoreAdapter()
        service = MemoryService(store)
        yield service
    else:  # sqlite
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_memory.db"
            store = SQLiteStoreAdapter(str(db_path))
            service = MemoryService(store)
            yield service
            store.close()


@pytest.mark.asyncio
async def test_full_user_preference_flow(memory_system):
    """E2E: Store and retrieve user preferences across sessions."""
    user_id = "test_user_001"
    namespace = ("companion", user_id, "preferences")

    # First session: Initialize with default
    default_prefs = "User prefers concise responses."
    prefs = await memory_system.get_memory(namespace, "style", default_prefs)
    assert prefs == default_prefs

    # User gives feedback: "Give me more details"
    updated_prefs = "User prefers detailed technical explanations."
    await memory_system.update_memory(namespace, "style", updated_prefs)

    # Second session: Retrieve learned preference
    retrieved = await memory_system.get_memory(namespace, "style")
    assert retrieved == updated_prefs


@pytest.mark.asyncio
async def test_multi_user_isolation(memory_system):
    """E2E: Ensure complete isolation between different users."""
    user1_ns = ("companion", "user_001", "prefs")
    user2_ns = ("companion", "user_002", "prefs")

    # User 1 sets preference
    await memory_system.update_memory(user1_ns, "theme", "dark_mode")

    # User 2 sets different preference
    await memory_system.update_memory(user2_ns, "theme", "light_mode")

    # Verify isolation
    user1_theme = await memory_system.get_memory(user1_ns, "theme")
    user2_theme = await memory_system.get_memory(user2_ns, "theme")

    assert user1_theme == "dark_mode"
    assert user2_theme == "light_mode"


@pytest.mark.asyncio
async def test_learning_from_feedback_flow(memory_system):
    """E2E: Learn from user feedback over multiple interactions."""
    user_id = "user_003"
    learning_ns = ("companion", user_id, "learning")

    # Track multiple feedback instances
    feedback_instances = [
        "User edited response to be more casual",
        "User asked for shorter responses",
        "User prefers bullet points over paragraphs",
    ]

    for i, feedback in enumerate(feedback_instances):
        await memory_system.update_memory(
            learning_ns,
            f"feedback_{i}",
            feedback,
        )

    # Extract pattern from feedback
    pattern = "User prefers casual, concise, bullet-point format."
    await memory_system.update_memory(learning_ns, "pattern", pattern)

    # Retrieve learned pattern
    learned = await memory_system.get_memory(learning_ns, "pattern")
    assert learned == pattern

    # Verify all feedback stored
    all_feedback = await memory_system.search_memories(learning_ns, limit=10)
    assert len(all_feedback) == 4  # 3 feedback + 1 pattern


@pytest.mark.asyncio
async def test_cross_session_context_persistence(memory_system):
    """E2E: Context persists across multiple sessions."""
    user_id = "user_004"
    session_ns = ("companion", user_id, "session_context")

    # Session 1: Discuss project
    await memory_system.update_memory(
        session_ns,
        "project",
        "Building AI chatbot with LangGraph",
    )

    # Session 2: Add more context
    await memory_system.update_memory(
        session_ns,
        "tech_stack",
        "Python, FastAPI, PostgreSQL",
    )

    # Session 3: Retrieve all context
    project = await memory_system.get_memory(session_ns, "project")
    tech = await memory_system.get_memory(session_ns, "tech_stack")

    assert project == "Building AI chatbot with LangGraph"
    assert tech == "Python, FastAPI, PostgreSQL"


@pytest.mark.asyncio
async def test_multi_tenant_complete_isolation(memory_system):
    """E2E: Multi-tenant with complete namespace isolation."""
    # Tenant A
    await memory_system.update_memory(
        ("tenant_a", "user_1", "prefs"),
        "language",
        "English",
    )
    await memory_system.update_memory(
        ("tenant_a", "user_1", "facts"),
        "location",
        "New York",
    )

    # Tenant B (same user ID)
    await memory_system.update_memory(
        ("tenant_b", "user_1", "prefs"),
        "language",
        "Japanese",
    )
    await memory_system.update_memory(
        ("tenant_b", "user_1", "facts"),
        "location",
        "Tokyo",
    )

    # Verify complete isolation
    a_lang = await memory_system.get_memory(
        ("tenant_a", "user_1", "prefs"),
        "language",
    )
    a_loc = await memory_system.get_memory(
        ("tenant_a", "user_1", "facts"),
        "location",
    )
    b_lang = await memory_system.get_memory(
        ("tenant_b", "user_1", "prefs"),
        "language",
    )
    b_loc = await memory_system.get_memory(
        ("tenant_b", "user_1", "facts"),
        "location",
    )

    assert a_lang == "English"
    assert a_loc == "New York"
    assert b_lang == "Japanese"
    assert b_loc == "Tokyo"


@pytest.mark.asyncio
async def test_memory_update_preserves_other_keys(memory_system):
    """E2E: Updating one key doesn't affect others in namespace."""
    namespace = ("companion", "user_005", "prefs")

    # Store multiple preferences
    await memory_system.update_memory(namespace, "theme", "dark")
    await memory_system.update_memory(namespace, "lang", "en")
    await memory_system.update_memory(namespace, "notif", "enabled")

    # Update only one
    await memory_system.update_memory(namespace, "theme", "light")

    # Verify others unchanged
    theme = await memory_system.get_memory(namespace, "theme")
    lang = await memory_system.get_memory(namespace, "lang")
    notif = await memory_system.get_memory(namespace, "notif")

    assert theme == "light"
    assert lang == "en"
    assert notif == "enabled"


@pytest.mark.asyncio
async def test_memory_search_with_multiple_keys(memory_system):
    """E2E: Search returns all memories in namespace."""
    namespace = ("companion", "user_006", "facts")

    facts = {
        "skill_1": "Python expert",
        "skill_2": "FastAPI proficient",
        "skill_3": "PostgreSQL advanced",
        "interest_1": "AI/ML",
        "interest_2": "DevOps",
    }

    for key, value in facts.items():
        await memory_system.update_memory(namespace, key, value)

    # Search all
    all_memories = await memory_system.search_memories(namespace, limit=10)

    assert len(all_memories) == 5
    assert "Python expert" in all_memories
    assert "AI/ML" in all_memories
