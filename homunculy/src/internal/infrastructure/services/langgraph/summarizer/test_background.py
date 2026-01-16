"""
Unit tests for BackgroundSummarizer.

Tests async summarization without blocking main response flow.
"""

import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from internal.infrastructure.services.langgraph.summarizer import (
    BackgroundSummarizer,
    create_background_summarizer,
)


class MockMessage:
    """Mock LangChain message for testing without langchain_core."""

    def __init__(self, content: str, msg_type: str = "human"):
        self.content = content
        self.type = msg_type


def mock_messages(*contents: str) -> Any:
    """Create mock messages list cast to Any to bypass type checking."""
    return cast(Any, [MockMessage(c) for c in contents])


class TestBackgroundSummarizer:
    """Test BackgroundSummarizer functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create mock LLM model."""
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=MagicMock(content="Test summary"))
        return model

    @pytest.fixture
    def summarizer(self, mock_model):
        """Create summarizer instance."""
        return BackgroundSummarizer(
            summarization_model=mock_model,
            max_tokens_before_summary=100,
            max_summary_tokens=50,
        )

    def test_should_summarize_below_threshold(self, summarizer):
        """Should not summarize when below token threshold."""
        messages = mock_messages("Hello")
        assert not summarizer.should_summarize(messages, token_count=50)

    def test_should_summarize_above_threshold(self, summarizer):
        """Should summarize when above token threshold."""
        messages = mock_messages("Hello")
        assert summarizer.should_summarize(messages, token_count=150)

    @pytest.mark.asyncio
    async def test_summarize_async_returns_task(self, summarizer):
        """summarize_async should return asyncio Task."""
        messages = mock_messages("Test message")

        task = await summarizer.summarize_async(
            thread_id="test-thread",
            messages=messages,
            existing_summary=None,
        )

        assert isinstance(task, asyncio.Task)
        result = await task
        assert result == "Test summary"

    @pytest.mark.asyncio
    async def test_summarize_with_existing_summary(self, summarizer, mock_model):
        """Should include existing summary in prompt."""
        messages = mock_messages("New message")
        existing = "Previous conversation about weather"

        task = await summarizer.summarize_async(
            thread_id="test-thread",
            messages=messages,
            existing_summary=existing,
        )

        await task

        # Check that ainvoke was called with prompt containing previous summary
        call_args = mock_model.ainvoke.call_args
        prompt_content = call_args[0][0][0].content
        assert "Previous summary" in prompt_content
        assert existing in prompt_content

    @pytest.mark.asyncio
    async def test_on_complete_callback(self, summarizer):
        """Should call on_complete callback when done."""
        callback = AsyncMock()
        messages = mock_messages("Test")

        task = await summarizer.summarize_async(
            thread_id="test-thread",
            messages=messages,
            existing_summary=None,
            on_complete=callback,
        )

        await task
        callback.assert_called_once_with("test-thread", "Test summary")

    @pytest.mark.asyncio
    async def test_wait_for_thread(self, summarizer):
        """wait_for_thread should return summary when complete."""
        messages = mock_messages("Test")

        await summarizer.summarize_async(
            thread_id="test-thread",
            messages=messages,
            existing_summary=None,
        )

        result = await summarizer.wait_for_thread("test-thread")
        assert result == "Test summary"

    @pytest.mark.asyncio
    async def test_wait_for_nonexistent_thread(self, summarizer):
        """wait_for_thread should return None for unknown thread."""
        result = await summarizer.wait_for_thread("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_cancel_all(self, summarizer):
        """cancel_all should cancel pending tasks."""
        # Create slow model
        slow_model = AsyncMock()

        async def slow_invoke(*args, **kwargs):
            await asyncio.sleep(10)
            return MagicMock(content="Never reached")

        slow_model.ainvoke = slow_invoke

        summarizer._model = slow_model
        messages = mock_messages("Test")

        await summarizer.summarize_async(
            thread_id="test-1",
            messages=messages,
            existing_summary=None,
        )
        await summarizer.summarize_async(
            thread_id="test-2",
            messages=messages,
            existing_summary=None,
        )

        assert summarizer.pending_task_count == 2

        await summarizer.cancel_all()
        assert summarizer.pending_task_count == 0

    @pytest.mark.asyncio
    async def test_format_messages_limits_context(self, summarizer):
        """Should only format last 10 messages."""
        messages = cast(Any, [MockMessage(f"Msg {i}") for i in range(20)])

        formatted = summarizer._format_messages(messages)
        lines = formatted.strip().split("\n")

        # Should have at most 10 lines
        assert len(lines) <= 10
        # Should contain last messages
        assert "Msg 19" in formatted


class TestBackgroundSummarizerFactory:
    """Test factory function."""

    def test_create_with_defaults(self):
        """Factory should create with default values."""
        model = MagicMock()
        summarizer = create_background_summarizer(model)

        assert summarizer.model == model
        assert summarizer.max_tokens_before_summary == 1024
        assert summarizer.max_summary_tokens == 128

    def test_create_with_custom_values(self):
        """Factory should accept custom values."""
        model = MagicMock()
        summarizer = create_background_summarizer(
            model=model,
            max_tokens_before_summary=500,
            max_summary_tokens=100,
        )

        assert summarizer.max_tokens_before_summary == 500
        assert summarizer.max_summary_tokens == 100


class TestBackgroundSummarizerIntegration:
    """Integration tests for background summarization."""

    @pytest.mark.asyncio
    async def test_non_blocking_response(self):
        """Main response should not wait for summarization."""
        # Create a slow model for summarization
        slow_model = AsyncMock()

        async def slow_invoke(*args, **kwargs):
            await asyncio.sleep(0.5)  # 500ms delay
            return MagicMock(content="Delayed summary")

        slow_model.ainvoke = slow_invoke

        summarizer = BackgroundSummarizer(
            summarization_model=slow_model,
            max_tokens_before_summary=10,
        )

        messages = mock_messages("Test")

        # Start summarization
        start_time = asyncio.get_event_loop().time()
        task = await summarizer.summarize_async(
            thread_id="test",
            messages=messages,
            existing_summary=None,
        )
        elapsed = asyncio.get_event_loop().time() - start_time

        # Should return immediately (non-blocking)
        assert elapsed < 0.1  # Much less than 500ms

        # Task should still be running
        assert not task.done()

        # Wait for completion
        await task
        assert task.done()

    @pytest.mark.asyncio
    async def test_multiple_threads_parallel(self):
        """Multiple threads can summarize in parallel."""
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=MagicMock(content="Summary"))

        summarizer = BackgroundSummarizer(
            summarization_model=model,
            max_tokens_before_summary=10,
        )

        messages = mock_messages("Test")

        # Start multiple summarizations
        task1 = await summarizer.summarize_async("thread-1", messages, None)
        task2 = await summarizer.summarize_async("thread-2", messages, None)
        task3 = await summarizer.summarize_async("thread-3", messages, None)

        # All should complete
        results = await asyncio.gather(task1, task2, task3)

        assert all(r == "Summary" for r in results)
        assert model.ainvoke.call_count == 3
