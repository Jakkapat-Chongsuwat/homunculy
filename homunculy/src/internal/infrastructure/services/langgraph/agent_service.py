"""
LangGraph Agent Service with Postgres-backed persistence.

Refactored to use smaller, focused modules:
- CheckpointerManager: Checkpoint initialization/lifecycle
- GraphManager: Graph caching and building
- ResponseBuilder: Response construction
- BackgroundSummarizer: Async summarization (optional)
"""

import asyncio
import os
from typing import Any, Dict, Optional, cast

from langchain_core.runnables.config import RunnableConfig

from common.logger import get_logger
from internal.domain.entities import AgentConfiguration, AgentResponse, AgentStatus
from internal.domain.exceptions import AgentExecutionException
from internal.domain.services import LLMService, TTSService, RAGService
from internal.infrastructure.services.langgraph.checkpointer import (
    CheckpointerManager,
    create_checkpointer_manager,
)
from internal.infrastructure.services.langgraph.exceptions import (
    GraphStateException,
    LLMAuthenticationException,
)
from internal.infrastructure.services.langgraph.graph_building import build_system_prompt
from internal.infrastructure.services.langgraph.graph import (
    GraphManager,
    ThreadResolver,
)
from internal.infrastructure.services.langgraph.response import (
    ResponseBuilder,
    create_response_builder,
)
from settings import (
    LLM_SUMMARIZATION_MAX_TOKENS,
    LLM_SUMMARIZATION_SUMMARY_TOKENS,
    LLM_SUMMARIZATION_TRIGGER_TOKENS,
)


logger = get_logger(__name__)


class LangGraphAgentService(LLMService):
    """
    LangGraph-based Agent service with Postgres-backed persistence.

    Uses modular components for maintainability:
    - CheckpointerManager for state persistence
    - GraphManager for graph lifecycle
    - ResponseBuilder for response construction
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = LLM_SUMMARIZATION_MAX_TOKENS,
        max_tokens_before_summary: int = LLM_SUMMARIZATION_TRIGGER_TOKENS,
        max_summary_tokens: int = LLM_SUMMARIZATION_SUMMARY_TOKENS,
        checkpointer: Any = None,
        tts_service: Optional[TTSService] = None,
        rag_service: Optional[RAGService] = None,
    ) -> None:
        """Initialize agent service."""
        resolved_key = api_key or os.getenv("LLM_OPENAI_API_KEY")
        if not resolved_key:
            raise LLMAuthenticationException(
                "OpenAI API key not provided",
                provider="openai",
            )
        self.api_key: str = resolved_key

        self.tts_service = tts_service
        self.rag_service = rag_service
        self._checkpointer_mgr = create_checkpointer_manager(checkpointer)
        self._graph_mgr: Optional[GraphManager] = None
        self._response_builder: Optional[ResponseBuilder] = None

        self._max_tokens = max_tokens
        self._max_tokens_before_summary = max_tokens_before_summary
        self._max_summary_tokens = max_summary_tokens

        logger.info(
            "LangGraphAgentService initialized",
            tts_enabled=tts_service is not None,
            rag_enabled=rag_service is not None,
        )

    async def _ensure_initialized(self) -> None:
        """Initialize all components on first use."""
        await self._checkpointer_mgr.ensure_initialized()

        if not self._graph_mgr:
            self._graph_mgr = GraphManager(
                api_key=self.api_key,
                checkpointer=self._checkpointer_mgr.checkpointer,
                tts_service=self.tts_service,
                rag_service=self.rag_service,
                max_tokens=self._max_tokens,
                max_tokens_before_summary=self._max_tokens_before_summary,
                max_summary_tokens=self._max_summary_tokens,
            )

        if not self._response_builder:
            self._response_builder = create_response_builder(
                tts_service=self.tts_service,
                storage_type=self._checkpointer_mgr.storage_type,
            )

    async def chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Execute chat with Postgres-backed persistence."""
        thread_id = "unknown"
        try:
            await self._ensure_initialized()

            thread_id = ThreadResolver.resolve(configuration, context)
            logger.info("Chat request", thread_id=thread_id)

            if not self._graph_mgr:
                raise AgentExecutionException("Graph manager not initialized")

            graph = await self._graph_mgr.get_or_build(configuration)

            response_text, summary_used = await self._execute_chat(
                graph, thread_id, configuration, message
            )

            audio = await self._maybe_generate_audio(context, response_text)

            if not self._response_builder:
                raise AgentExecutionException("Response builder not initialized")

            return self._response_builder.build_success(
                configuration=configuration,
                thread_id=thread_id,
                response_text=response_text,
                summary_used=summary_used,
                checkpointer_name=type(self._checkpointer_mgr.checkpointer).__name__,
                audio_response=audio,
            )

        except Exception as exc:
            logger.error("Chat error", thread_id=thread_id, error=str(exc))
            if self._response_builder:
                return self._response_builder.build_error(str(exc))
            return AgentResponse(
                message=f"Error: {exc}",
                confidence=0.0,
                status=AgentStatus.ERROR,
            )

    async def _execute_chat(
        self,
        graph: Any,
        thread_id: str,
        configuration: AgentConfiguration,
        message: str,
    ) -> tuple[str, bool]:
        """Execute graph and return response."""
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_core.runnables.config import RunnableConfig

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        # Check existing state
        is_first = await self._is_first_message(graph, cast(RunnableConfig, config))

        # Build messages
        messages = []
        if is_first:
            system_prompt = build_system_prompt(configuration)
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))

        # Invoke graph
        result = await graph.ainvoke({"messages": messages}, config)

        # Extract response
        response_text = self._extract_response(result)
        summary_used = bool(result.get("context", {}).get("running_summary"))

        return response_text, summary_used

    async def _is_first_message(self, graph: Any, config: RunnableConfig) -> bool:
        """Check if this is first message in thread."""
        try:
            state = await graph.aget_state(config)
            return len(state.values.get("messages", [])) == 0
        except Exception as e:
            logger.warning("Could not get state", error=str(e))
            configurable = config.get("configurable") or {}
            thread_id = configurable.get("thread_id") if isinstance(configurable, dict) else None
            raise GraphStateException(
                f"Failed to get state: {e}",
                thread_id=thread_id,
            ) from e

    def _extract_response(self, result: dict) -> str:
        """Extract response text from graph result."""
        response = result.get("response", "")

        if not response:
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                response = getattr(last_msg, 'content', '') or ""

        return response or "No response generated"

    async def _maybe_generate_audio(
        self,
        context: Optional[Dict[str, Any]],
        text: str,
    ) -> Optional[Dict[str, Any]]:
        """Generate audio if requested in context."""
        if not context or not context.get("include_audio"):
            return None
        if not self._response_builder:
            return None
        return await self._response_builder.generate_audio(text)

    async def stream_chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Stream chat response as text chunks."""
        thread_id = "unknown"
        chunk_count = 0

        try:
            await self._ensure_initialized()

            thread_id = ThreadResolver.resolve(configuration, context)
            logger.info("Starting LLM stream", thread_id=thread_id)

            if not self._graph_mgr:
                raise AgentExecutionException("Graph manager not initialized")

            # Enable tools for streaming to allow RAG and TTS tools
            graph = await self._graph_mgr.get_or_build(configuration, bind_tools=True)

            async for chunk in self._stream_graph(graph, thread_id, configuration, message):
                chunk_count += 1
                yield chunk

            logger.info(
                "LLM stream completed",
                thread_id=thread_id,
                chunks=chunk_count,
            )

        except asyncio.CancelledError:
            logger.warning("Stream cancelled", thread_id=thread_id)
            raise
        except Exception as exc:
            logger.error("Stream error", thread_id=thread_id, error=str(exc))
            raise AgentExecutionException(
                f"Streaming failed: {exc}",
                thread_id=thread_id,
            ) from exc

    async def _stream_graph(
        self,
        graph: Any,
        thread_id: str,
        configuration: AgentConfiguration,
        message: str,
    ):
        """Stream graph execution with tool support.

        When tools are enabled, we use ainvoke to let the graph fully execute
        (including any tool calls), then stream the final response character by character.
        This ensures RAG and other tools work correctly while still providing streaming output.
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        from langchain_core.runnables.config import RunnableConfig

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        is_first = await self._is_first_message(graph, cast(RunnableConfig, config))

        messages = []
        if is_first:
            system_prompt = build_system_prompt(configuration)
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))

        # Use ainvoke to allow full tool execution, then stream the result
        result = await graph.ainvoke({"messages": messages}, config)

        # Extract final response from messages
        response_text = ""
        result_messages = result.get("messages", [])
        if result_messages:
            # Find the last AI message (not a tool message)
            for msg in reversed(result_messages):
                if isinstance(msg, AIMessage) and not getattr(msg, 'tool_calls', None):
                    response_text = getattr(msg, 'content', '') or ""
                    break

        if not response_text:
            response_text = result.get("response", "No response generated")

        # Stream the response character by character for smooth output
        # Use small chunks for natural streaming feel
        chunk_size = 10
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i : i + chunk_size]
            yield chunk
            await asyncio.sleep(0.01)  # Small delay for streaming effect

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._checkpointer_mgr.cleanup()
