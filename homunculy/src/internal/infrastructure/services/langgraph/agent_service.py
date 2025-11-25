"""LangGraph Agent Service with Postgres-backed persistence."""

import asyncio
import os
from typing import Any, Dict, Optional, TYPE_CHECKING

from common.logger import get_logger
from settings.tts import tts_settings

from langgraph.checkpoint.memory import MemorySaver

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver as AsyncPostgresSaverType
else:
    AsyncPostgresSaverType = object

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg import AsyncConnection
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool
    HAS_POSTGRES_CHECKPOINT = True
except ImportError:
    HAS_POSTGRES_CHECKPOINT = False
    AsyncPostgresSaver = type('AsyncPostgresSaver', (), {})
    AsyncConnection = type('AsyncConnection', (), {})
    AsyncConnectionPool = type('AsyncConnectionPool', (), {})

from internal.domain.entities import AgentConfiguration, AgentResponse, AgentStatus
from internal.domain.services import LLMService, TTSService
from internal.domain.exceptions import AgentExecutionException
from internal.infrastructure.services.langgraph.exceptions import (
    CheckpointerConnectionException,
    CheckpointerSetupException,
    LLMAuthenticationException,
    GraphStateException,
)
from internal.infrastructure.services.langgraph.graph_building import (
    build_conversation_graph_with_summarization,
    create_langchain_model,
    build_system_prompt,
)
from settings import DATABASE_URI


logger = get_logger(__name__)


class LangGraphAgentService(LLMService):
    """
    LangGraph-based Agent service with Postgres-backed persistence.
    
    Uses AsyncPostgresSaver for stateless checkpoint storage, enabling
    horizontal scaling and container restart resilience.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_tokens: int = 256,
        max_tokens_before_summary: int = 1024,
        max_summary_tokens: int = 128,
        checkpointer = None,
        tts_service: Optional[TTSService] = None,
    ) -> None:
        """
        Initialize agent service with checkpoint configuration.
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            max_tokens: Max tokens in LLM response
            max_tokens_before_summary: Token threshold for summarization
            max_summary_tokens: Max tokens in summary
            checkpointer: Optional checkpointer for testing
            tts_service: Optional TTS service for voice capabilities
        """
        self.api_key = api_key or os.getenv("LLM_OPENAI_API_KEY")
        if not self.api_key:
            raise LLMAuthenticationException(
                "OpenAI API key not provided. Set LLM_OPENAI_API_KEY environment variable.",
                provider="openai"
            )

        self.max_tokens = max_tokens
        self.max_tokens_before_summary = max_tokens_before_summary
        self.max_summary_tokens = max_summary_tokens
        self.tts_service = tts_service
        
        self._checkpointer = checkpointer
        self._checkpointer_initialized = checkpointer is not None
        self._postgres_pool: Optional[Any] = None
        self._graph_cache: Dict[str, Any] = {}
        
        logger.info(
            "LangGraphAgentService initialized",
            checkpointer="provided" if checkpointer else "will_initialize",
            postgres_available=HAS_POSTGRES_CHECKPOINT,
            tts_enabled=tts_service is not None
        )
    
    async def _ensure_checkpointer(self) -> None:
        """
        Initialize Postgres checkpointer on first use.
        
        Creates persistent connection and calls AsyncPostgresSaver.setup()
        to create required database tables. Raises exceptions in production mode.
        
        Raises:
            CheckpointerConnectionException: If connection times out
            CheckpointerSetupException: If setup fails
        """
        if self._checkpointer_initialized:
            return
        
        logger.info("Initializing checkpointer")
        
        if HAS_POSTGRES_CHECKPOINT and DATABASE_URI:
            try:
                db_uri = DATABASE_URI.replace('+asyncpg', '')
                db_host = db_uri.split('@')[1] if '@' in db_uri else 'unknown'
                logger.info("Connecting to Postgres", db_host=db_host)
                
                # Production-grade connection pooling
                self._postgres_pool = AsyncConnectionPool(  # type: ignore[attr-defined]
                    db_uri,
                    min_size=2,
                    max_size=10,
                    kwargs={
                        "autocommit": True,
                        "prepare_threshold": 0,
                        "row_factory": dict_row
                    }
                )
                
                self._checkpointer = AsyncPostgresSaver(self._postgres_pool)  # type: ignore[arg-type]
                
                logger.info("Setting up checkpoint tables")
                await asyncio.wait_for(
                    self._checkpointer.setup(),  # type: ignore[attr-defined]
                    timeout=30.0
                )
                
                logger.info(
                    "AsyncPostgresSaver initialized successfully",
                    pool_min_size=2,
                    pool_max_size=10
                )
                
            except asyncio.TimeoutError as e:
                logger.error("Checkpoint connection timeout", error=str(e))
                raise CheckpointerConnectionException(
                    "Connection to PostgreSQL timed out",
                    storage_type="postgres"
                ) from e
                
            except Exception as e:
                logger.error("Failed to initialize checkpointer", error=str(e), exc_info=True)
                raise CheckpointerSetupException(
                    f"Failed to setup PostgreSQL checkpointer: {e}",
                    storage_type="postgres"
                ) from e
        else:
            reason = "package not installed" if not HAS_POSTGRES_CHECKPOINT else "no DATABASE_URI"
            logger.warning("Postgres unavailable, using MemorySaver", reason=reason)
            self._checkpointer = MemorySaver()
        
        self._checkpointer_initialized = True
        logger.info("Checkpointer ready", checkpointer_type=type(self._checkpointer).__name__)

    def _get_config_signature(self, configuration: AgentConfiguration) -> str:
        """Generate unique signature for graph caching."""
        return f"{configuration.model_name}:{configuration.temperature}:{configuration.max_tokens}"

    def _resolve_thread_id(
        self,
        configuration: AgentConfiguration,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """
        Resolve checkpoint thread_id from context.
        
        Priority: session_id > user_id:agent_id > default
        """
        if not context:
            return "default"

        session_id = context.get("session_id")
        if session_id:
            return f"session:{session_id}"

        user_id = context.get("user_id")
        if not user_id:
            return "default"

        agent_scope = context.get("agent_id") or configuration.model_name
        return f"user:{user_id}:{agent_scope}"

    async def _get_or_build_graph(
        self,
        configuration: AgentConfiguration,
        system_prompt: str,
    ):
        """
        Retrieve cached graph or build new one with checkpointer and optional TTS tools.
        
        All graphs share the same checkpointer instance for state persistence.
        If TTS service is available, TTS tools are automatically registered.
        """
        await self._ensure_checkpointer()
        
        config_sig = self._get_config_signature(configuration)
        
        if config_sig in self._graph_cache:
            logger.debug("Using cached graph", config_sig=config_sig)
            return self._graph_cache[config_sig]
        
        logger.info("Building graph", config_sig=config_sig, tts_enabled=self.tts_service is not None)
        
        assert self.api_key is not None, "API key must be set"
        
        base_llm = create_langchain_model(
            self.api_key, 
            configuration.model_name,
            configuration.temperature,
            configuration.max_tokens,
        )
        
        # Register TTS tools if TTS service is available
        if self.tts_service:
            from internal.infrastructure.services.langgraph.agent_tools import (
                create_text_to_speech_tool,
                create_list_voices_tool,
            )
            
            tts_tool = create_text_to_speech_tool(self.tts_service)
            list_voices_tool = create_list_voices_tool(self.tts_service)
            
            # Bind tools to the model
            base_llm = base_llm.bind_tools([tts_tool, list_voices_tool])
            logger.info("TTS tools bound to agent", tools=["text_to_speech", "list_voices"])
        
        graph = build_conversation_graph_with_summarization(
            base_llm,
            system_prompt,
            self.max_tokens,
            self.max_tokens_before_summary,
            self.max_summary_tokens,
            checkpointer=self._checkpointer,
        )
        
        self._graph_cache[config_sig] = graph
        logger.info("Graph compiled and cached", config_sig=config_sig)
        return graph

    async def chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Execute chat interaction with Postgres-backed persistence.
        
        Conversation state is loaded from and persisted to Postgres automatically.
        Service remains stateless and can restart without data loss.
        
        If TTS service is available, automatically generates audio for the response.
        """
        try:
            self._validate_api_key()
            
            thread_id = self._resolve_thread_id(configuration, context)
            logger.info(
                "Chat request",
                thread_id=thread_id,
                message_preview=message[:50]
            )
            
            system_prompt = build_system_prompt(configuration)
            graph = await self._get_or_build_graph(configuration, system_prompt)
            
            is_first_message = await self._check_if_first_message(graph, thread_id)
            messages_to_add = self._build_message_list(system_prompt, message, is_first_message, thread_id)
            
            response_text, summary_used = await self._execute_graph(graph, thread_id, messages_to_add)
            
            # Auto-generate TTS audio only if requested via context flag
            audio_response = None
            if self.tts_service and context and context.get("include_audio", False):
                audio_response = await self._generate_response_audio(response_text)
            
            return self._build_success_response(
                configuration, thread_id, response_text, summary_used, audio_response
            )

        except Exception as exc:
            logger.error(
                "Chat error",
                thread_id=thread_id if 'thread_id' in locals() else "unknown",
                error=str(exc),
                exc_info=True
            )
            return self._build_error_response(str(exc))
    
    def _validate_api_key(self) -> None:
        """Validate API key is set."""
        if not self.api_key:
            raise LLMAuthenticationException(
                "API key is required",
                provider="openai"
            )
    
    async def _check_if_first_message(self, graph, thread_id: str) -> bool:
        """Check if this is the first message in conversation."""
        from langchain_core.runnables.config import RunnableConfig
        
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        
        try:
            existing_state = await graph.aget_state(config)
            existing_messages = existing_state.values.get("messages", [])
            is_first = len(existing_messages) == 0
            
            self._log_conversation_state(thread_id, is_first, existing_messages)
            return is_first
            
        except GraphStateException:
            raise
        except Exception as e:
            logger.warning(
                "Could not get existing state",
                thread_id=thread_id,
                error=str(e)
            )
            # Wrap in domain exception
            raise GraphStateException(
                f"Failed to retrieve conversation state: {str(e)}",
                thread_id=thread_id
            ) from e
    
    def _log_conversation_state(
        self, 
        thread_id: str, 
        is_first_message: bool, 
        existing_messages: list
    ) -> None:
        """Log conversation state for debugging."""
        storage_type = self._get_storage_type()
        logger.info(
            "Thread state",
            thread_id=thread_id,
            first_message=is_first_message,
            existing_messages_count=len(existing_messages),
            checkpointer=type(self._checkpointer).__name__,
            storage=storage_type
        )
        
        if existing_messages:
            msg_ids = [getattr(msg, 'id', 'no-id') for msg in existing_messages[:3]]
            logger.debug("Existing message IDs", message_ids=msg_ids, count=len(existing_messages))
    
    def _build_message_list(
        self, 
        system_prompt: str, 
        message: str, 
        is_first_message: bool,
        thread_id: str
    ) -> list:
        """Build list of messages to add to graph."""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages_to_add = []
        
        if is_first_message:
            logger.info("First message in thread, adding system prompt", thread_id=thread_id)
            messages_to_add.append(SystemMessage(content=system_prompt))
        
        messages_to_add.append(HumanMessage(content=message))
        logger.debug("Adding messages to graph", message_count=len(messages_to_add))
        
        return messages_to_add
    
    async def _execute_graph(
        self, 
        graph, 
        thread_id: str, 
        messages_to_add: list
    ) -> tuple[str, bool]:
        """Execute LangGraph and return response."""
        from langchain_core.runnables.config import RunnableConfig
        from typing import cast
        
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        input_update = cast(Any, {"messages": messages_to_add})

        logger.info("Invoking graph", thread_id=thread_id)
        result = await graph.ainvoke(input_update, config)
        logger.info("Graph invocation complete", thread_id=thread_id)

        await self._log_post_invocation_state(graph, thread_id, config)
        self._check_graph_errors(result, thread_id)
        
        # Extract response from result or messages
        response_text = result.get("response", "")
        
        # If response is empty, check if there are tool calls in messages
        if not response_text:
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    response_text = last_message.content or ""
                    
                # Check for tool calls
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    tool_info = []
                    for tool_call in last_message.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        tool_info.append(f"Called tool: {tool_name}")
                    if tool_info:
                        response_text = response_text + " " + " ".join(tool_info) if response_text else " ".join(tool_info)
        
        if not response_text:
            response_text = "No response generated"
        
        summary_used = bool(result.get("context", {}).get("running_summary"))
        
        logger.info(
            "Response generated",
            thread_id=thread_id,
            response_length=len(response_text),
            summary_used=summary_used
        )
        
        return response_text, summary_used
    
    async def _log_post_invocation_state(self, graph, thread_id: str, config) -> None:
        """Log conversation state after invocation."""
        try:
            post_state = await graph.aget_state(config)
            post_messages = post_state.values.get("messages", [])
            logger.info(
                "Thread post-invocation state",
                thread_id=thread_id,
                messages_count=len(post_messages)
            )
        except Exception as e:
            logger.warning("Could not get post-invocation state", error=str(e))
    
    def _check_graph_errors(self, result: dict, thread_id: str) -> None:
        """Check for graph execution errors."""
        if result.get("error"):
            error_msg = result["error"]
            logger.error(
                "Graph execution error",
                thread_id=thread_id,
                error=error_msg
            )
            raise AgentExecutionException(
                f"LangGraph execution error: {error_msg}",
                thread_id=thread_id
            )
    
    def _get_storage_type(self) -> str:
        """Get current storage type."""
        if HAS_POSTGRES_CHECKPOINT and type(self._checkpointer).__name__ == 'AsyncPostgresSaver':
            return 'postgres'
        return 'memory'
    
    async def _generate_response_audio(self, text: str) -> Optional[dict]:
        """
        Generate TTS audio for response text.
        
        Returns:
            Dictionary with AudioResponse structure or None if generation fails
        """
        if not self.tts_service:
            return None
            
        try:
            import base64
            
            # Clean text for TTS (remove tool call messages)
            clean_text = text.replace("Called tool:", "").replace("text_to_speech", "").strip()
            
            if not clean_text or len(clean_text) < 3:
                logger.debug("Skipping TTS - text too short or empty")
                return None
            
            logger.info("Generating TTS audio for response", text_length=len(clean_text))
            
            # Use default voice from settings
            voice_id = tts_settings.default_voice_id
            audio_bytes = await self.tts_service.synthesize(
                text=clean_text,
                voice_id=voice_id,
                model_id=tts_settings.elevenlabs_model_id,
                stability=tts_settings.default_stability,
                similarity_boost=tts_settings.default_similarity_boost,
                style=tts_settings.default_style,
                use_speaker_boost=tts_settings.default_use_speaker_boost
            )
            
            # Encode to base64 for JSON transport
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            logger.info(
                "TTS audio generated",
                audio_size_kb=len(audio_bytes) / 1024,
                base64_size_kb=len(audio_base64) / 1024
            )
            
            # Return strongly-typed audio response structure
            return {
                "data": audio_base64,
                "format": "mp3",
                "encoding": "base64",
                "size_bytes": len(audio_bytes),
                "voice_id": voice_id,
                "duration_ms": None  # Could calculate from audio if needed
            }
            
        except Exception as e:
            logger.error("Failed to generate response audio", error=str(e), exc_info=True)
            return None
    
    def _build_success_response(
        self,
        configuration: AgentConfiguration,
        thread_id: str,
        response_text: str,
        summary_used: bool,
        audio_response: Optional[dict] = None
    ) -> AgentResponse:
        """Build successful response with strongly-typed metadata and optional audio."""
        storage_type = self._get_storage_type()
        
        metadata = {
            "model_used": configuration.model_name,
            "tokens_used": None,  # Could track if LangChain provides callback
            "execution_time_ms": None,  # Could track with timer
            "tools_called": [],  # Could extract from graph state
            "checkpointer_state": None,
            "thread_id": thread_id,
            "storage_type": storage_type,
            # Legacy fields for backward compatibility
            "model": configuration.model_name,
            "temperature": configuration.temperature,
            "max_tokens": configuration.max_tokens,
            "orchestrator": "langgraph",
            "memory": "langmem",
            "summary_used": summary_used,
            "checkpointer": type(self._checkpointer).__name__,
            "storage": storage_type,
        }
        
        # Include strongly-typed audio if generated
        if audio_response:
            metadata["audio"] = audio_response
        
        return AgentResponse(
            message=response_text,
            confidence=0.95,
            reasoning=f"Generated by {configuration.model_name} via LangGraph",
            metadata=metadata,
            status=AgentStatus.COMPLETED,
        )
    
    def _build_error_response(self, error_message: str) -> AgentResponse:
        """Build error response."""
        return AgentResponse(
            message=f"Error: {error_message}",
            confidence=0.0,
            reasoning="Failed to communicate with LLM via LangGraph",
            metadata={"error": error_message},
            status=AgentStatus.ERROR,
        )
    
    async def cleanup(self) -> None:
        """Cleanup resources including Postgres connection pool."""
        if self._postgres_pool:
            try:
                await self._postgres_pool.close()  # type: ignore[attr-defined]
                logger.info("AsyncPostgresSaver connection pool closed")
            except Exception as e:
                logger.error("Error closing connection pool", error=str(e))
