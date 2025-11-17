"""LangGraph LLM Service Implementation with short-term + summary memory."""

import asyncio
import logging
import os
from datetime import timedelta
from typing import Any, Dict, List, Optional

from internal.domain.entities import AgentConfiguration, AgentResponse, AgentStatus
from internal.domain.services import LLMService

from ..langgraph.factories import (
    ConversationState,
    build_conversation_graph,
    create_primary_agent,
    create_summarizer_agent,
)
from ..memory.short_term import (
    ConversationSummaryStore,
    MemoryConfig,
    ShortTermMemoryStore,
    SummaryEntry,
)


logger = logging.getLogger(__name__)

class LangGraphLLMService(LLMService):
    """LangGraph-based LLM service implementation with layered memory."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        memory_max_messages: int = 8,
        memory_ttl_seconds: int = 900,
        summary_batch_size: int = 6,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set LLM_OPENAI_API_KEY environment variable.")

        self._memory = ShortTermMemoryStore(
            MemoryConfig(
                max_messages=memory_max_messages,
                ttl=timedelta(seconds=memory_ttl_seconds) if memory_ttl_seconds else None,
            )
        )
        self._summary_store = ConversationSummaryStore()
        self._summary_batch_size = max(4, summary_batch_size)
        self._summary_tasks: Dict[str, asyncio.Task] = {}

    def _resolve_memory_key(
        self,
        configuration: AgentConfiguration,
        context: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        if not context:
            return None

        session_id = context.get("session_id")
        if session_id:
            return f"session:{session_id}"

        user_id = context.get("user_id")
        if not user_id:
            return None

        agent_scope = context.get("agent_id") or configuration.model_name
        return f"user:{user_id}:{agent_scope}"

    async def _load_short_term_context(self, memory_key: Optional[str]) -> List[Dict[str, str]]:
        if not memory_key:
            return []

        return await self._memory.read(memory_key)

    async def _persist_short_term_context(
        self,
        memory_key: Optional[str],
        user_message: str,
        assistant_message: Optional[str],
    ) -> None:
        if not memory_key:
            return

        await self._memory.append(memory_key, "user", user_message)

        if assistant_message:
            await self._memory.append(memory_key, "assistant", assistant_message)

    async def _maybe_trigger_summary(
        self,
        memory_key: Optional[str],
        configuration: AgentConfiguration,
    ) -> None:
        if not memory_key:
            return

        total_messages = self._memory.get_total_count(memory_key)
        summary_entry = await self._summary_store.get(memory_key)
        if total_messages - summary_entry.message_count < self._summary_batch_size:
            return

        existing_task = self._summary_tasks.get(memory_key)
        if existing_task and not existing_task.done():
            return

        self._summary_tasks[memory_key] = asyncio.create_task(
            self._summarize_conversation(memory_key, configuration)
        )

    async def _summarize_conversation(
        self,
        memory_key: str,
        configuration: AgentConfiguration,
    ) -> None:
        try:
            history = await self._memory.read(memory_key)
            if not history:
                return

            summary_entry = await self._summary_store.get(memory_key)
            summarizer = create_summarizer_agent(self.api_key, configuration)
            prompt = self._build_summary_prompt(summary_entry, history)
            result = await summarizer.run(prompt)
            summary_text = result.output.strip()
            total_messages = self._memory.get_total_count(memory_key)
            await self._summary_store.save(memory_key, summary_text, total_messages)
        except Exception as exc:  # pragma: no cover - logging side effect
            logger.warning("Failed to summarize conversation %s: %s", memory_key, exc)
        finally:
            self._summary_tasks.pop(memory_key, None)

    def _build_summary_prompt(
        self,
        summary_entry: SummaryEntry,
        history: List[Dict[str, str]],
    ) -> str:
        formatted_history = "\n".join(
            f"{msg.get('role', 'user').title()}: {msg.get('content', '')}"
            for msg in history
        )

        previous_summary = summary_entry.summary or "(no summary yet)"
        return (
            "You maintain a rolling memory for a multi-user conversation. "
            "Update the summary to reflect ALL important facts, intents, and commitments. "
            "Keep it under 200 words, neutral tone, first person for the assistant.\n\n"
            f"Previous summary:\n{previous_summary}\n\n"
            f"Recent exchanges:\n{formatted_history}\n\n"
            "Return only the updated summary text."
        )

    async def chat(
        self,
        configuration: AgentConfiguration,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        try:
            memory_key = self._resolve_memory_key(configuration, context)
            history = await self._load_short_term_context(memory_key)
            summary_entry = await self._summary_store.get(memory_key) if memory_key else SummaryEntry()
            summary_text = summary_entry.summary.strip() or None

            agent = create_primary_agent(self.api_key, configuration)
            graph = build_conversation_graph(agent)

            initial_state: ConversationState = {
                "messages": [*history, {"role": "user", "content": message}],
                "system_prompt": configuration.system_prompt,
                "summary": summary_text,
                "response": None,
                "error": None,
            }

            result = await graph.ainvoke(initial_state)

            if result.get("error"):
                return AgentResponse(
                    message=f"Error: {result['error']}",
                    confidence=0.0,
                    reasoning="LangGraph execution error",
                    metadata={"error": result["error"]},
                    status=AgentStatus.ERROR,
                )

            response_text = result.get("response", "No response generated")

            await self._persist_short_term_context(memory_key, message, response_text)
            await self._maybe_trigger_summary(memory_key, configuration)

            return AgentResponse(
                message=response_text,
                confidence=0.95,
                reasoning=f"Generated by {configuration.model_name} via LangGraph orchestration with PydanticAI",
                metadata={
                    "model": configuration.model_name,
                    "temperature": configuration.temperature,
                    "max_tokens": configuration.max_tokens,
                    "orchestrator": "langgraph",
                    "provider": "pydantic_ai",
                    "summary_used": bool(summary_text),
                },
                status=AgentStatus.COMPLETED,
            )

        except Exception as exc:
            return AgentResponse(
                message=f"Error: {str(exc)}",
                confidence=0.0,
                reasoning="Failed to communicate with LLM via LangGraph",
                metadata={"error": str(exc)},
                status=AgentStatus.ERROR,
            )
