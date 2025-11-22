"""LangGraph Agent Service with Postgres-backed persistence."""

import asyncio
import logging
import os
from typing import Any, Dict, Optional, TYPE_CHECKING

from langgraph.checkpoint.memory import MemorySaver

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver as AsyncPostgresSaverType
else:
    AsyncPostgresSaverType = object

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg import AsyncConnection
    from psycopg.rows import dict_row
    HAS_POSTGRES_CHECKPOINT = True
except ImportError:
    HAS_POSTGRES_CHECKPOINT = False
    AsyncPostgresSaver = type('AsyncPostgresSaver', (), {})
    AsyncConnection = type('AsyncConnection', (), {})

from internal.domain.entities import AgentConfiguration, AgentResponse, AgentStatus
from internal.domain.services import LLMService
from internal.domain.exceptions import AgentExecutionException
from internal.infrastructure.llm.exceptions import LLMAuthenticationException
from internal.infrastructure.agents.exceptions import (
    CheckpointerConnectionException,
    CheckpointerSetupException,
)
from internal.infrastructure.llm.langgraph.factories import (
    build_conversation_graph_with_summarization,
    create_langchain_model,
    build_system_prompt,
)
from settings import DATABASE_URI


logger = logging.getLogger(__name__)


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
    ) -> None:
        """
        Initialize agent service with checkpoint configuration.
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            max_tokens: Max tokens in LLM response
            max_tokens_before_summary: Token threshold for summarization
            max_summary_tokens: Max tokens in summary
            checkpointer: Optional checkpointer for testing
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
        
        self._checkpointer = checkpointer
        self._checkpointer_initialized = checkpointer is not None
        self._postgres_connection: Optional[Any] = None
        self._graph_cache: Dict[str, Any] = {}
        
        logger.info(
            f"LangGraphAgentService initialized | "
            f"checkpointer={'provided' if checkpointer else 'will_initialize'} | "
            f"postgres_available={HAS_POSTGRES_CHECKPOINT}"
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
                logger.info(f"Connecting to Postgres: {db_uri.split('@')[1]}")
                
                self._postgres_connection = await asyncio.wait_for(
                    AsyncConnection.connect(  # type: ignore[attr-defined]
                        db_uri,
                        autocommit=True,
                        prepare_threshold=0,
                        row_factory=dict_row  # type: ignore[arg-type]
                    ),
                    timeout=30.0
                )
                
                self._checkpointer = AsyncPostgresSaver(self._postgres_connection)  # type: ignore[arg-type]
                
                logger.info("Setting up checkpoint tables")
                await asyncio.wait_for(
                    self._checkpointer.setup(),  # type: ignore[attr-defined]
                    timeout=30.0
                )
                
                logger.info("AsyncPostgresSaver initialized successfully")
                
            except asyncio.TimeoutError as e:
                logger.error(f"Checkpoint connection timeout: {e}")
                raise CheckpointerConnectionException(
                    "Connection to PostgreSQL timed out",
                    storage_type="postgres"
                ) from e
                
            except Exception as e:
                logger.error(f"Failed to initialize checkpointer: {e}")
                raise CheckpointerSetupException(
                    f"Failed to setup PostgreSQL checkpointer: {e}",
                    storage_type="postgres"
                ) from e
        else:
            reason = "package not installed" if not HAS_POSTGRES_CHECKPOINT else "no DATABASE_URI"
            logger.warning(f"Postgres unavailable ({reason}), using MemorySaver")
            self._checkpointer = MemorySaver()
        
        self._checkpointer_initialized = True
        logger.info(f"Checkpointer ready: {type(self._checkpointer).__name__}")

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
        Retrieve cached graph or build new one with checkpointer.
        
        All graphs share the same checkpointer instance for state persistence.
        """
        await self._ensure_checkpointer()
        
        config_sig = self._get_config_signature(configuration)
        
        if config_sig in self._graph_cache:
            logger.debug(f"Using cached graph: {config_sig}")
            return self._graph_cache[config_sig]
        
        logger.info(f"Building graph: {config_sig}")
        
        assert self.api_key is not None, "API key must be set"
        
        llm = create_langchain_model(
            self.api_key, 
            configuration.model_name,
            configuration.temperature,
            configuration.max_tokens,
        )
        
        graph = build_conversation_graph_with_summarization(
            llm,
            system_prompt,
            self.max_tokens,
            self.max_tokens_before_summary,
            self.max_summary_tokens,
            checkpointer=self._checkpointer,
        )
        
        self._graph_cache[config_sig] = graph
        logger.info(f"Graph compiled and cached: {config_sig}")
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
        """
        try:
            self._validate_api_key()
            
            thread_id = self._resolve_thread_id(configuration, context)
            logger.info(f"Chat request | thread={thread_id} | message={message[:50]}...")
            
            system_prompt = build_system_prompt(configuration)
            graph = await self._get_or_build_graph(configuration, system_prompt)
            
            is_first_message = await self._check_if_first_message(graph, thread_id)
            messages_to_add = self._build_message_list(system_prompt, message, is_first_message, thread_id)
            
            response_text, summary_used = await self._execute_graph(graph, thread_id, messages_to_add)
            
            return self._build_success_response(
                configuration, thread_id, response_text, summary_used
            )

        except Exception as exc:
            logger.exception(f"Chat error for thread '{thread_id}': {exc}")
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
            
        except Exception as e:
            logger.warning(f"Could not get existing state for thread '{thread_id}': {e}")
            return True
    
    def _log_conversation_state(
        self, 
        thread_id: str, 
        is_first_message: bool, 
        existing_messages: list
    ) -> None:
        """Log conversation state for debugging."""
        storage_type = self._get_storage_type()
        logger.info(
            f"Thread '{thread_id}' state | "
            f"first_message={is_first_message} | "
            f"existing_messages={len(existing_messages)} | "
            f"checkpointer={type(self._checkpointer).__name__} | "
            f"storage={storage_type}"
        )
        
        if existing_messages:
            msg_ids = [getattr(msg, 'id', 'no-id') for msg in existing_messages[:3]]
            logger.debug(f"Existing message IDs (first 3): {msg_ids}")
    
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
            logger.info(f"First message in thread '{thread_id}', adding system prompt")
            messages_to_add.append(SystemMessage(content=system_prompt))
        
        messages_to_add.append(HumanMessage(content=message))
        logger.debug(f"Adding {len(messages_to_add)} messages to graph input")
        
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

        logger.info(f"Invoking graph | thread={thread_id}")
        result = await graph.ainvoke(input_update, config)
        logger.info(f"Graph invocation complete | thread={thread_id}")

        await self._log_post_invocation_state(graph, thread_id, config)
        self._check_graph_errors(result, thread_id)
        
        response_text = result.get("response", "No response generated")
        summary_used = bool(result.get("context", {}).get("running_summary"))
        
        logger.info(
            f"Response generated | thread={thread_id} | "
            f"length={len(response_text)} | summary={summary_used}"
        )
        
        return response_text, summary_used
    
    async def _log_post_invocation_state(self, graph, thread_id: str, config) -> None:
        """Log conversation state after invocation."""
        try:
            post_state = await graph.aget_state(config)
            post_messages = post_state.values.get("messages", [])
            logger.info(f"Thread '{thread_id}' post-invocation | messages={len(post_messages)}")
        except Exception as e:
            logger.warning(f"Could not get post-invocation state: {e}")
    
    def _check_graph_errors(self, result: dict, thread_id: str) -> None:
        """Check for graph execution errors."""
        if result.get("error"):
            error_msg = result["error"]
            logger.error(f"Graph execution error | thread={thread_id} | error={error_msg}")
            raise AgentExecutionException(
                f"LangGraph execution error: {error_msg}",
                thread_id=thread_id
            )
    
    def _get_storage_type(self) -> str:
        """Get current storage type."""
        if HAS_POSTGRES_CHECKPOINT and type(self._checkpointer).__name__ == 'AsyncPostgresSaver':
            return 'postgres'
        return 'memory'
    
    def _build_success_response(
        self,
        configuration: AgentConfiguration,
        thread_id: str,
        response_text: str,
        summary_used: bool
    ) -> AgentResponse:
        """Build successful response."""
        storage_type = self._get_storage_type()
        
        return AgentResponse(
            message=response_text,
            confidence=0.95,
            reasoning=f"Generated by {configuration.model_name} via LangGraph",
            metadata={
                "model": configuration.model_name,
                "temperature": configuration.temperature,
                "max_tokens": configuration.max_tokens,
                "orchestrator": "langgraph",
                "memory": "langmem",
                "summary_used": summary_used,
                "thread_id": thread_id,
                "checkpointer": type(self._checkpointer).__name__,
                "storage": storage_type,
            },
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
        """Cleanup resources including Postgres connection."""
        if self._postgres_connection:
            try:
                await self._postgres_connection.close()  # type: ignore[attr-defined]
                logger.info("AsyncPostgresSaver connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
