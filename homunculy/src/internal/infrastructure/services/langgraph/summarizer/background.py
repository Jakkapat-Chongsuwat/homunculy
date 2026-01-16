"""
Background Summarizer for LangGraph conversations.

Runs conversation summarization asynchronously without blocking
the main response flow. Updates checkpoint state in the background.
"""

import asyncio
from typing import Any, Dict, Optional, Sequence

from common.logger import get_logger
from langchain_core.messages import BaseMessage, SystemMessage

logger = get_logger(__name__)


class BackgroundSummarizer:
    """
    Asynchronous conversation summarizer.

    Runs summarization in the background, allowing the main chat
    response to return immediately while state is updated later.
    """

    def __init__(
        self,
        summarization_model: Any,
        max_tokens_before_summary: int = 1024,
        max_summary_tokens: int = 128,
    ) -> None:
        """
        Initialize background summarizer.

        Args:
            summarization_model: LLM model for generating summaries
            max_tokens_before_summary: Token threshold to trigger summarization
            max_summary_tokens: Maximum tokens in generated summary
        """
        self._model = summarization_model
        self._max_tokens_before_summary = max_tokens_before_summary
        self._max_summary_tokens = max_summary_tokens
        self._pending_tasks: Dict[str, asyncio.Task[str]] = {}

    @property
    def model(self) -> Any:
        """Get summarization model."""
        return self._model

    @property
    def max_tokens_before_summary(self) -> int:
        """Get token threshold for summarization."""
        return self._max_tokens_before_summary

    @property
    def max_summary_tokens(self) -> int:
        """Get max summary token limit."""
        return self._max_summary_tokens

    @property
    def pending_task_count(self) -> int:
        """Get count of pending tasks."""
        return len(self._pending_tasks)

    def should_summarize(self, messages: Sequence[BaseMessage], token_count: int) -> bool:
        """Check if conversation needs summarization."""
        return token_count > self._max_tokens_before_summary

    async def summarize_async(
        self,
        thread_id: str,
        messages: Sequence[BaseMessage],
        existing_summary: Optional[str],
        on_complete: Optional[Any] = None,
    ) -> asyncio.Task[str]:
        """
        Start background summarization task.

        Args:
            thread_id: Conversation thread identifier
            messages: Messages to summarize
            existing_summary: Previous summary to extend
            on_complete: Callback when summarization completes

        Returns:
            Background task handle
        """
        task = asyncio.create_task(
            self._run_summarization(thread_id, messages, existing_summary, on_complete)
        )
        self._pending_tasks[thread_id] = task
        return task

    async def _run_summarization(
        self,
        thread_id: str,
        messages: Sequence[BaseMessage],
        existing_summary: Optional[str],
        on_complete: Optional[Any],
    ) -> str:
        """Execute summarization in background."""
        try:
            logger.info(
                "Background summarization started",
                thread_id=thread_id,
                message_count=len(messages),
            )

            prompt = self._build_summary_prompt(messages, existing_summary)
            result = await self._model.ainvoke([SystemMessage(content=prompt)])
            summary = result.content if hasattr(result, "content") else str(result)

            logger.info(
                "Background summarization complete",
                thread_id=thread_id,
                summary_length=len(summary),
            )

            if on_complete:
                await on_complete(thread_id, summary)

            return summary

        except Exception as e:
            logger.error(
                "Background summarization failed",
                thread_id=thread_id,
                error=str(e),
            )
            raise
        finally:
            self._pending_tasks.pop(thread_id, None)

    def _build_summary_prompt(
        self,
        messages: Sequence[BaseMessage],
        existing_summary: Optional[str],
    ) -> str:
        """Build prompt for summarization."""
        conversation_text = self._format_messages(messages)

        if existing_summary:
            return (
                f"Previous summary:\n{existing_summary}\n\n"
                f"New messages:\n{conversation_text}\n\n"
                "Create an updated summary combining the previous summary "
                "with the new messages. Be concise but preserve key context."
            )

        return (
            f"Summarize this conversation concisely:\n{conversation_text}\n\n"
            "Focus on key topics, decisions, and context needed for future replies."
        )

    def _format_messages(self, messages: Sequence[BaseMessage]) -> str:
        """Format messages for summary prompt."""
        lines = []
        for msg in messages[-10:]:  # Last 10 messages for context
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", str(msg))
            lines.append(f"{role}: {content[:200]}")
        return "\n".join(lines)

    async def wait_for_thread(self, thread_id: str) -> Optional[str]:
        """Wait for pending summarization to complete."""
        task = self._pending_tasks.get(thread_id)
        if task:
            return await task
        return None

    async def cancel_all(self) -> None:
        """Cancel all pending summarization tasks."""
        for task in self._pending_tasks.values():
            task.cancel()
        self._pending_tasks.clear()


def create_background_summarizer(
    model: Any,
    max_tokens_before_summary: int = 1024,
    max_summary_tokens: int = 128,
) -> BackgroundSummarizer:
    """Factory function for BackgroundSummarizer."""
    return BackgroundSummarizer(
        summarization_model=model,
        max_tokens_before_summary=max_tokens_before_summary,
        max_summary_tokens=max_summary_tokens,
    )
