"""E2E tests for memory tools in LangGraph agent.

Tests the full integration:
- Memory tools (search_memory, save_memory)
- LangGraph graph compilation with store
- Tool invocation by LLM (mocked)
- Store persistence across invocations
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore

from infrastructure.adapters.store import SQLiteStoreAdapter
from infrastructure.adapters.tools.memory import save_memory, search_memory


@pytest.fixture(params=["inmemory", "sqlite"])
def store(request, tmp_path):
    """Create store for e2e testing."""
    if request.param == "inmemory":
        return InMemoryStore()
    else:
        db_file = tmp_path / "test_memory_tools.db"
        return SQLiteStoreAdapter(str(db_file))


@pytest.fixture
def mock_llm():
    """Mock LLM that can decide to call memory tools."""

    async def mock_ainvoke(messages):
        last = messages[-1].content if messages else ""

        if "remember" in last.lower():
            content = last.replace("Remember ", "").replace("remember ", "")
            return AIMessage(
                "",
                tool_calls=[
                    {
                        "name": "save_memory",
                        "args": {"content": content},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            )
        elif "what do i like" in last.lower():
            return AIMessage(
                "",
                tool_calls=[
                    {
                        "name": "search_memory",
                        "args": {"query": "food preferences"},
                        "id": "call_2",
                        "type": "tool_call",
                    }
                ],
            )
        else:
            return AIMessage("I'm here to help!")

    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=mock_ainvoke)
    return llm


def build_agent_with_memory(llm, store):
    """Build LangGraph agent with memory tools."""
    tools = [search_memory, save_memory]
    llm_with_tools = MagicMock()
    llm_with_tools.ainvoke = llm.ainvoke

    async def chat(state):
        return {"messages": [await llm_with_tools.ainvoke(state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("chat", chat)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "chat")
    builder.add_conditional_edges("chat", tools_condition)
    builder.add_edge("tools", "chat")

    return builder.compile(store=store)


@pytest.mark.asyncio
async def test_agent_saves_memory_when_asked(store, mock_llm):
    """E2E: Agent uses save_memory tool when user asks to remember."""
    graph = build_agent_with_memory(mock_llm, store)
    config: RunnableConfig = {"configurable": {"user_id": "user_1"}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage("Remember that I like pizza")]},
        config=config,
    )

    messages = result["messages"]
    tool_msg = next(m for m in messages if hasattr(m, "tool_call_id"))
    assert "Saved" in tool_msg.content

    items = store.search(("memories", "user_1"))
    assert any("pizza" in i.value["data"] for i in items)


@pytest.mark.asyncio
async def test_agent_searches_memory_when_asked(store, mock_llm):
    """E2E: Agent uses search_memory tool to recall information."""
    store.put(("memories", "user_1"), "k1", {"data": "User likes pizza"})

    graph = build_agent_with_memory(mock_llm, store)
    config: RunnableConfig = {"configurable": {"user_id": "user_1"}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage("What do I like to eat?")]},
        config=config,
    )

    messages = result["messages"]
    tool_msg = next(m for m in messages if hasattr(m, "tool_call_id"))
    assert "pizza" in tool_msg.content.lower()


@pytest.mark.asyncio
async def test_memory_persists_across_graph_invocations(store, mock_llm):
    """E2E: Memory persists across separate graph invocations."""
    graph = build_agent_with_memory(mock_llm, store)
    config: RunnableConfig = {"configurable": {"user_id": "user_2"}}

    await graph.ainvoke(
        {"messages": [HumanMessage("Remember I like sushi")]},
        config=config,
    )

    result = await graph.ainvoke(
        {"messages": [HumanMessage("What do I like?")]},
        config=config,
    )

    messages = result["messages"]
    tool_msg = next(m for m in messages if hasattr(m, "tool_call_id"))
    assert "sushi" in tool_msg.content.lower()


@pytest.mark.asyncio
async def test_memory_isolated_by_user(store, mock_llm):
    """E2E: Memory is isolated per user_id."""
    graph = build_agent_with_memory(mock_llm, store)
    config_a: RunnableConfig = {"configurable": {"user_id": "user_a"}}
    config_b: RunnableConfig = {"configurable": {"user_id": "user_b"}}

    await graph.ainvoke(
        {"messages": [HumanMessage("Remember I like tacos")]},
        config=config_a,
    )

    await graph.ainvoke(
        {"messages": [HumanMessage("Remember I like ramen")]},
        config=config_b,
    )

    result_a = await graph.ainvoke(
        {"messages": [HumanMessage("What do I like?")]},
        config=config_a,
    )

    result_b = await graph.ainvoke(
        {"messages": [HumanMessage("What do I like?")]},
        config=config_b,
    )

    tool_a = next(m for m in result_a["messages"] if hasattr(m, "tool_call_id"))
    tool_b = next(m for m in result_b["messages"] if hasattr(m, "tool_call_id"))

    assert "tacos" in tool_a.content.lower()
    assert "ramen" in tool_b.content.lower()
    assert "ramen" not in tool_a.content.lower()
    assert "tacos" not in tool_b.content.lower()


@pytest.mark.asyncio
async def test_search_returns_no_memories_when_empty(store, mock_llm):
    """E2E: search_memory returns appropriate message when no memories."""
    graph = build_agent_with_memory(mock_llm, store)
    config: RunnableConfig = {"configurable": {"user_id": "empty_user"}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage("What do I like?")]},
        config=config,
    )

    messages = result["messages"]
    tool_msg = next(m for m in messages if hasattr(m, "tool_call_id"))
    assert "No relevant memories found" in tool_msg.content
