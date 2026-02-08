"""E2E tests for MemoryService (Store layer)."""

import pytest

from application.services import MemoryService
from infrastructure.adapters.store import InMemoryStoreAdapter, SQLiteStoreAdapter


@pytest.fixture(params=["inmemory", "sqlite"])
def memory_system(request, tmp_path):
    """Create complete memory system for e2e testing."""
    if request.param == "inmemory":
        store = InMemoryStoreAdapter()
        return MemoryService(store)
    else:
        db_file = tmp_path / "test_memory.db"
        store = SQLiteStoreAdapter(str(db_file))
        return MemoryService(store)


@pytest.mark.asyncio
async def test_full_user_preference_flow(memory_system):
    """E2E: Store and retrieve user preferences across sessions."""
    user_id = "test_user_001"
    namespace = ("companion", user_id, "preferences")

    default_prefs = "User prefers concise responses."
    prefs = memory_system.get_memory(namespace, "style", default_prefs)
    assert prefs == default_prefs

    updated_prefs = "User prefers detailed technical explanations."
    memory_system.update_memory(namespace, "style", updated_prefs)

    retrieved = memory_system.get_memory(namespace, "style")
    assert retrieved == updated_prefs


@pytest.mark.asyncio
async def test_multi_user_isolation(memory_system):
    """E2E: Ensure complete isolation between different users."""
    user1_ns = ("companion", "user_001", "prefs")
    user2_ns = ("companion", "user_002", "prefs")

    memory_system.update_memory(user1_ns, "theme", "dark_mode")
    memory_system.update_memory(user2_ns, "theme", "light_mode")

    user1_theme = memory_system.get_memory(user1_ns, "theme")
    user2_theme = memory_system.get_memory(user2_ns, "theme")

    assert user1_theme == "dark_mode"
    assert user2_theme == "light_mode"


@pytest.mark.asyncio
async def test_learning_from_feedback_flow(memory_system):
    """E2E: Learn from user feedback over multiple interactions."""
    user_id = "user_003"
    learning_ns = ("companion", user_id, "learning")

    feedback_instances = [
        "User edited response to be more casual",
        "User asked for shorter responses",
        "User prefers bullet points over paragraphs",
    ]

    for i, feedback in enumerate(feedback_instances):
        key = f"feedback_{i + 1}"
        memory_system.update_memory(learning_ns, key, feedback)

    pattern = "User prefers casual, concise, bullet-point format."
    memory_system.update_memory(learning_ns, "pattern", pattern)

    learned = memory_system.get_memory(learning_ns, "pattern")
    assert learned == pattern

    all_feedback = memory_system.search_memories(learning_ns, limit=10)
    assert len(all_feedback) == 4


@pytest.mark.asyncio
async def test_cross_session_context_persistence(memory_system):
    """E2E: Context persists across multiple sessions."""
    user_id = "user_004"
    session_ns = ("companion", user_id, "session_context")

    memory_system.update_memory(
        session_ns,
        "project",
        "Building AI chatbot with LangGraph",
    )

    memory_system.update_memory(
        session_ns,
        "tech_stack",
        "Python, FastAPI, PostgreSQL",
    )

    project = memory_system.get_memory(session_ns, "project")
    tech = memory_system.get_memory(session_ns, "tech_stack")

    assert project == "Building AI chatbot with LangGraph"
    assert tech == "Python, FastAPI, PostgreSQL"


@pytest.mark.asyncio
async def test_multi_tenant_complete_isolation(memory_system):
    """E2E: Multi-tenant with complete namespace isolation."""
    memory_system.update_memory(
        ("tenant_a", "user_1", "prefs"),
        "language",
        "English",
    )
    memory_system.update_memory(
        ("tenant_a", "user_1", "facts"),
        "location",
        "New York",
    )

    memory_system.update_memory(
        ("tenant_b", "user_1", "prefs"),
        "language",
        "Japanese",
    )
    memory_system.update_memory(
        ("tenant_b", "user_1", "facts"),
        "location",
        "Tokyo",
    )

    a_lang = memory_system.get_memory(
        ("tenant_a", "user_1", "prefs"),
        "language",
    )
    a_loc = memory_system.get_memory(
        ("tenant_a", "user_1", "facts"),
        "location",
    )
    b_lang = memory_system.get_memory(
        ("tenant_b", "user_1", "prefs"),
        "language",
    )
    b_loc = memory_system.get_memory(
        ("tenant_b", "user_1", "facts"),
        "location",
    )

    assert a_lang == "English"
    assert a_loc == "New York"
    assert b_lang == "Japanese"
    assert b_loc == "Tokyo"
