"""
Graph management for LangGraph agent service.

Handles graph caching, building, and configuration-based compilation.
"""

from typing import Any, Dict, List, Optional

from common.logger import get_logger
from langchain_core.tools import BaseTool

from internal.domain.entities import AgentConfiguration
from internal.domain.services import RAGService, TTSService
from internal.infrastructure.services.langgraph.graph_building import (
    build_conversation_graph_with_summarization,
    build_system_prompt,
    create_langchain_model,
)

logger = get_logger(__name__)


class GraphManager:
    """
    Manages LangGraph compilation and caching.

    Caches compiled graphs by configuration signature to avoid
    recompilation overhead. Supports optional TTS and RAG tool binding.
    """

    def __init__(
        self,
        api_key: str,
        checkpointer: Any,
        tts_service: Optional[TTSService] = None,
        rag_service: Optional[RAGService] = None,
        max_tokens: int = 256,
        max_tokens_before_summary: int = 1024,
        max_summary_tokens: int = 128,
    ) -> None:
        """
        Initialize graph manager.

        Args:
            api_key: OpenAI API key
            checkpointer: LangGraph checkpointer instance
            tts_service: Optional TTS service for voice tools
            rag_service: Optional RAG service for document search
            max_tokens: Max tokens after summarization
            max_tokens_before_summary: Threshold for summarization
            max_summary_tokens: Max tokens in summary
        """
        self._api_key = api_key
        self._checkpointer = checkpointer
        self._tts_service = tts_service
        self._rag_service = rag_service
        self._max_tokens = max_tokens
        self._max_tokens_before_summary = max_tokens_before_summary
        self._max_summary_tokens = max_summary_tokens
        self._cache: Dict[str, Any] = {}

    def update_checkpointer(self, checkpointer: Any) -> None:
        """Update checkpointer (clears cache)."""
        self._checkpointer = checkpointer
        self._cache.clear()

    async def get_or_build(
        self,
        configuration: AgentConfiguration,
        bind_tools: bool = True,
    ) -> Any:
        """
        Get cached graph or build new one.

        Args:
            configuration: Agent configuration
            bind_tools: Whether to bind TTS tools

        Returns:
            Compiled LangGraph
        """
        cache_key = self._make_cache_key(configuration, bind_tools)

        if cache_key in self._cache:
            logger.debug("Using cached graph", key=cache_key)
            return self._cache[cache_key]

        graph = await self._build_graph(configuration, bind_tools)
        self._cache[cache_key] = graph

        logger.info("Graph compiled and cached", key=cache_key)
        return graph

    def _make_cache_key(
        self,
        configuration: AgentConfiguration,
        bind_tools: bool,
    ) -> str:
        """Generate cache key from configuration."""
        return (
            f"{configuration.model_name}:"
            f"{configuration.temperature}:"
            f"{configuration.max_tokens}:"
            f"tools={bind_tools}"
        )

    async def _build_graph(
        self,
        configuration: AgentConfiguration,
        bind_tools: bool,
    ) -> Any:
        """Build new LangGraph instance."""
        system_prompt = build_system_prompt(configuration)

        base_llm = create_langchain_model(
            self._api_key,
            configuration.model_name,
            configuration.temperature,
            configuration.max_tokens,
        )

        # Collect tools
        tools: List[BaseTool] = []
        if bind_tools:
            tools = self._get_tools()
            if tools:
                # Bind tools to LLM for function calling
                base_llm = base_llm.bind_tools(tools)

        return build_conversation_graph_with_summarization(
            base_llm,
            system_prompt,
            self._max_tokens,
            self._max_tokens_before_summary,
            self._max_summary_tokens,
            checkpointer=self._checkpointer,
            tools=tools if tools else None,
        )

    def _get_tools(self) -> List[BaseTool]:
        """Collect all available tools."""
        tools: List[BaseTool] = []

        # Add TTS tools if available
        if self._tts_service:
            from internal.infrastructure.services.langgraph.agent_tools import (
                create_list_voices_tool,
            )

            tools.append(create_list_voices_tool(self._tts_service))
            logger.info("TTS tools added", tools=["list_voices"])

        # Add RAG tool if available
        if self._rag_service:
            from internal.infrastructure.services.langgraph.agent_tools import (
                create_rag_search_tool,
            )

            tools.append(create_rag_search_tool(self._rag_service))
            logger.info("RAG tools added", tools=["search_documents"])

        return tools

    def clear_cache(self) -> None:
        """Clear graph cache."""
        self._cache.clear()


def create_graph_manager(
    api_key: str,
    checkpointer: Any,
    tts_service: Optional[TTSService] = None,
    rag_service: Optional[RAGService] = None,
    max_tokens: int = 256,
    max_tokens_before_summary: int = 1024,
    max_summary_tokens: int = 128,
) -> GraphManager:
    """Factory function for GraphManager."""
    return GraphManager(
        api_key=api_key,
        checkpointer=checkpointer,
        tts_service=tts_service,
        rag_service=rag_service,
        max_tokens=max_tokens,
        max_tokens_before_summary=max_tokens_before_summary,
        max_summary_tokens=max_summary_tokens,
    )
