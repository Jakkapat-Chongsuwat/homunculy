"""Graph manager for LangGraph workflows."""

from typing import Any

from common.logger import get_logger
from domain.entities import AgentConfiguration

logger = get_logger(__name__)


class GraphManager:
    """Manages LangGraph workflow instances."""

    def __init__(
        self,
        llm: Any,
        checkpointer: Any,
        store: Any = None,
        build_fn=None,
    ) -> None:
        self._llm = llm
        self._checkpointer = checkpointer
        self._store = store
        self._build_fn = build_fn or _default_build_graph
        self._cache: dict[str, Any] = {}

    async def get_or_build(
        self,
        config: AgentConfiguration,
        bind_tools: bool = False,
    ) -> Any:
        """Get cached graph or build new one."""
        key = _cache_key(config, bind_tools)
        if key not in self._cache:
            self._cache[key] = await self._build(config, bind_tools)
        return self._cache[key]

    async def _build(self, config: AgentConfiguration, bind_tools: bool) -> Any:
        """Build new graph instance."""
        logger.debug("Building graph", model=config.model_name, tools=bind_tools)
        return await self._build_fn(
            llm=self._llm,
            checkpointer=self._checkpointer,
            store=self._store,
            config=config,
            bind_tools=bind_tools,
        )

    def clear_cache(self) -> None:
        """Clear graph cache."""
        self._cache.clear()


def _cache_key(config: AgentConfiguration, bind_tools: bool) -> str:
    """Generate cache key from config."""
    return f"{config.model_name}:{config.provider.value}:{bind_tools}"


async def _default_build_graph(
    llm: Any,
    checkpointer: Any,
    store: Any,
    config: AgentConfiguration,
    bind_tools: bool,
) -> Any:
    """Default LangGraph chat graph builder."""
    if bind_tools:
        return _build_tool_graph(llm, checkpointer, store)
    return _build_simple_graph(llm, checkpointer, store)


def _build_simple_graph(llm: Any, checkpointer: Any, store: Any) -> Any:
    """Build graph without tool support."""
    from langgraph.graph import END, START, StateGraph

    from infrastructure.adapters.llm.state import GraphState

    async def chat(state: GraphState) -> dict:
        return {"messages": [await llm.ainvoke(state["messages"])]}

    graph = StateGraph(GraphState)
    graph.add_node("chat", chat)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile(checkpointer=checkpointer, store=store)


def _build_tool_graph(llm: Any, checkpointer: Any, store: Any) -> Any:
    """Build graph with memory tools bound to LLM."""
    from langgraph.graph import START, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    from infrastructure.adapters.llm.state import GraphState
    from infrastructure.adapters.tools.memory import save_memory, search_memory

    tools = [search_memory, save_memory]
    llm_with_tools = llm.bind_tools(tools)

    async def chat(state: GraphState) -> dict:
        return {"messages": [await llm_with_tools.ainvoke(state["messages"])]}

    graph = StateGraph(GraphState)
    graph.add_node("chat", chat)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "chat")
    graph.add_conditional_edges("chat", tools_condition)
    graph.add_edge("tools", "chat")
    return graph.compile(checkpointer=checkpointer, store=store)


def create_graph_manager(
    llm: Any,
    checkpointer: Any,
    store: Any = None,
    build_fn=None,
) -> GraphManager:
    """Factory to create graph manager."""
    return GraphManager(llm, checkpointer, store, build_fn)
