"""Unit tests for Supervisor Adapter - Output Selection Logic.

Tests behavior through the public LangGraphSupervisorAdapter.delegate() method
which coordinates all internal message parsing and content selection logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.interfaces.orchestration import OrchestrationInput
from infrastructure.adapters.orchestration.supervisor.adapter import (
    LangGraphSupervisorAdapter,
)


@pytest.fixture
def sample_input() -> OrchestrationInput:
    """Create sample orchestration input."""
    return OrchestrationInput(message="Hello", session_id="test-session")


@pytest.fixture
def adapter() -> LangGraphSupervisorAdapter:
    """Create adapter with test API key."""
    return LangGraphSupervisorAdapter(api_key="test-key", model="gpt-4o-mini")


async def _delegate_with_messages(
    adapter: LangGraphSupervisorAdapter,
    messages: list,
    input_: OrchestrationInput,
) -> str:
    """Helper to delegate with mocked messages and return result."""
    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock(return_value={"messages": messages})

    with patch.object(adapter, "_get_or_build_supervisor", return_value=mock_graph):
        result = await adapter.delegate("supervisor", input_)
    return result.message


class TestAdapterMessageExtraction:
    """Test message content extraction via delegate."""

    @pytest.mark.asyncio
    async def test_extracts_content_from_object(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Extract content from object with content attr."""
        result = await _delegate_with_messages(
            adapter, [_make_msg("ai", "helper", "Hello world")], sample_input
        )
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_extracts_content_from_dict(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Extract content from dict message format."""
        result = await _delegate_with_messages(
            adapter, [{"role": "assistant", "content": "Hello dict"}], sample_input
        )
        assert result == "Hello dict"


class TestAdapterVisibility:
    """Test user visibility logic via delegate."""

    @pytest.mark.asyncio
    async def test_tool_message_not_visible(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Tool messages should not be selected over assistant messages."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "companion", "Real response"),
                _make_msg("tool", "search", "tool output"),
            ],
            sample_input,
        )
        assert result == "Real response"

    @pytest.mark.asyncio
    async def test_supervisor_not_visible(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Supervisor messages should not be selected over agent messages."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "companion", "Agent response"),
                _make_msg("ai", "supervisor", "Supervisor internal"),
            ],
            sample_input,
        )
        assert result == "Agent response"

    @pytest.mark.asyncio
    async def test_assistant_visible(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Regular assistant messages should be selected."""
        result = await _delegate_with_messages(
            adapter, [_make_msg("assistant", "companion", "Hi there!")], sample_input
        )
        assert result == "Hi there!"

    @pytest.mark.asyncio
    async def test_ai_visible(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """AI type messages should be selected."""
        result = await _delegate_with_messages(
            adapter, [_make_msg("ai", "helper", "Hello from AI")], sample_input
        )
        assert result == "Hello from AI"


class TestAdapterHandoffDetection:
    """Test handoff message filtering via delegate."""

    @pytest.mark.asyncio
    async def test_transferring_to_skipped(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """'Transferring to X' messages should be skipped for real content."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "companion", "Real answer"),
                _make_msg("ai", "supervisor", "Transferring to companion"),
            ],
            sample_input,
        )
        assert result == "Real answer"

    @pytest.mark.asyncio
    async def test_transferring_back_skipped(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """'Transferring back to supervisor' should be skipped."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "companion", "Helpful response"),
                _make_msg("ai", "supervisor", "Transferring back to supervisor"),
            ],
            sample_input,
        )
        assert result == "Helpful response"

    @pytest.mark.asyncio
    async def test_handing_off_skipped(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """'Handing off to X' should be skipped."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "researcher", "Found the info"),
                _make_msg("ai", "supervisor", "Handing off to researcher"),
            ],
            sample_input,
        )
        assert result == "Found the info"

    @pytest.mark.asyncio
    async def test_normal_message_selected(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Normal messages without handoff phrases should be selected."""
        result = await _delegate_with_messages(
            adapter, [_make_msg("ai", "helper", "Hello! How can I help?")], sample_input
        )
        assert result == "Hello! How can I help?"

    @pytest.mark.asyncio
    async def test_handoff_case_insensitive(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Handoff detection is case insensitive."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "companion", "Actual response"),
                _make_msg("ai", "supervisor", "TRANSFERRING TO AGENT"),
            ],
            sample_input,
        )
        assert result == "Actual response"


class TestAdapterContentSelection:
    """Test content selection from message list via delegate."""

    @pytest.mark.asyncio
    async def test_selects_last_visible_assistant(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Should select last visible assistant message."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("user", "user", "Hi"),
                _make_msg("ai", "companion", "Hello! I'm here to help."),
                _make_msg("ai", "supervisor", "Transferring back to supervisor"),
            ],
            sample_input,
        )
        assert result == "Hello! I'm here to help."

    @pytest.mark.asyncio
    async def test_skips_tool_messages(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Should skip tool messages."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("user", "", "Search for cats"),
                _make_msg("tool", "search", '{"results": ["cat1", "cat2"]}'),
                _make_msg("ai", "researcher", "I found 2 cats!"),
            ],
            sample_input,
        )
        assert result == "I found 2 cats!"

    @pytest.mark.asyncio
    async def test_skips_supervisor_handoff(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Should skip supervisor handoff messages."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("user", "", "Hello"),
                _make_msg("ai", "companion", "Hi there! Nice to meet you."),
                _make_msg("ai", "supervisor", "Transferring back to supervisor"),
            ],
            sample_input,
        )
        assert result == "Hi there! Nice to meet you."

    @pytest.mark.asyncio
    async def test_fallback_to_any_content(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Should fallback to any non-handoff content when all are handoffs."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("ai", "supervisor", "Transferring to companion"),
                _make_msg("ai", "supervisor", "Transferring back to supervisor"),
            ],
            sample_input,
        )
        # Last message is returned as final fallback
        assert "Transferring" in result

    @pytest.mark.asyncio
    async def test_complex_conversation(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Test a realistic multi-turn conversation."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("user", "", "What is 2+2?"),
                _make_msg("ai", "supervisor", "Transferring to math_expert"),
                _make_msg("tool", "transfer_to_math_expert", ""),
                _make_msg("ai", "math_expert", "2 + 2 equals 4!"),
                _make_msg("ai", "supervisor", "Transferring back to supervisor"),
            ],
            sample_input,
        )
        assert result == "2 + 2 equals 4!"


class TestAdapterEdgeCases:
    """Test edge cases for output conversion."""

    @pytest.mark.asyncio
    async def test_empty_messages(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Empty messages should return empty output."""
        result = await _delegate_with_messages(adapter, [], sample_input)
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_subagent_response(
        self, adapter: LangGraphSupervisorAdapter, sample_input: OrchestrationInput
    ) -> None:
        """Should return subagent response, not handoff."""
        result = await _delegate_with_messages(
            adapter,
            [
                _make_msg("user", "", "Hi"),
                _make_msg("ai", "companion", "Hello friend!"),
                _make_msg("ai", "supervisor", "Transferring back to supervisor"),
            ],
            sample_input,
        )
        assert result == "Hello friend!"


def _make_msg(role: str, name: str, content: str) -> MagicMock:
    """Create a mock message."""
    msg = MagicMock()
    msg.type = role
    msg.name = name
    msg.content = content
    return msg
