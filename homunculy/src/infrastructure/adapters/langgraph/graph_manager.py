"""Graph manager for LangGraph workflows."""

from typing import Any

from common.logger import get_logger
from domain.entities import AgentConfiguration

logger = get_logger(__name__)


class GraphManager:
    """Manages LangGraph workflow instances."""

    def __init__(
        self,
        api_key: str,
        checkpointer: Any,
        build_fn=None,
    ) -> None:
        self._api_key = api_key
        self._checkpointer = checkpointer
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
            api_key=self._api_key,
            checkpointer=self._checkpointer,
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
    api_key: str,
    checkpointer: Any,
    config: AgentConfiguration,
    bind_tools: bool,
) -> Any:
    """Default LangGraph chat graph builder.

    This encapsulates all LangGraph/LangChain imports in infrastructure layer.
    """
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph
    from pydantic import SecretStr

    from infrastructure.adapters.langgraph.state import GraphState

    llm = ChatOpenAI(
        api_key=SecretStr(api_key),
        model=config.model_name or "gpt-4o-mini",
    )

    async def chat(state: GraphState) -> dict:
        return {"messages": [await llm.ainvoke(state["messages"])]}

    graph = StateGraph(GraphState)
    graph.add_node("chat", chat)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile(checkpointer=checkpointer)


def create_graph_manager(
    api_key: str,
    checkpointer: Any,
    build_fn=None,
) -> GraphManager:
    """Factory to create graph manager."""
    return GraphManager(api_key, checkpointer, build_fn)
