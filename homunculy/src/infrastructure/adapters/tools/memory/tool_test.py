"""Tests for memory tools via compiled graph (public API)."""

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore

from infrastructure.adapters.tools.memory.tool import save_memory, search_memory

TOOLS = [search_memory, save_memory]
NAMESPACE = ("memories", "u1")
CONFIG: RunnableConfig = {"configurable": {"user_id": "u1"}}


def _build_tool_graph(store: InMemoryStore):
    """Compile a minimal graph with ToolNode and store."""
    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "tools")
    return builder.compile(store=store)


def _make_tool_call(name: str, args: dict) -> AIMessage:
    """Create AIMessage with a single tool call."""
    call = {"name": name, "args": args, "id": "tc1", "type": "tool_call"}
    return AIMessage("", tool_calls=[call])


def _invoke(store, name, args, config: RunnableConfig | None = None):
    """Invoke tool through compiled graph."""
    graph = _build_tool_graph(store)
    msg = _make_tool_call(name, args)
    result = graph.invoke({"messages": [msg]}, config=config if config is not None else CONFIG)
    return result["messages"][-1].content


class TestSearchMemory:
    """Tests for search_memory tool."""

    def test_returns_stored_data(self):
        store = InMemoryStore()
        store.put(NAMESPACE, "k1", {"data": "User likes pizza"})

        content = _invoke(store, "search_memory", {"query": "food"})
        assert "User likes pizza" in content

    def test_returns_no_memories_message(self):
        store = InMemoryStore()

        content = _invoke(store, "search_memory", {"query": "anything"})
        assert content == "No relevant memories found."

    def test_isolates_by_user_id(self):
        store = InMemoryStore()
        store.put(("memories", "other"), "k1", {"data": "secret"})

        content = _invoke(store, "search_memory", {"query": "secret"})
        assert "secret" not in content


class TestSaveMemory:
    """Tests for save_memory tool."""

    def test_persists_content_to_store(self):
        store = InMemoryStore()

        content = _invoke(store, "save_memory", {"content": "I like sushi"})

        assert "Saved" in content
        items = store.search(NAMESPACE)
        assert any("I like sushi" in i.value["data"] for i in items)

    def test_defaults_user_id_when_missing(self):
        store = InMemoryStore()

        _invoke(store, "save_memory", {"content": "test"}, config={})

        items = store.search(("memories", "default"))
        assert len(items) == 1
