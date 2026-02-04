"""Unit tests for Supervisor Adapter - Output Selection Logic."""

from unittest.mock import MagicMock

import pytest

from infrastructure.adapters.orchestration.supervisor.adapter import (
    _is_handoff_message,
    _is_user_visible,
    _message_content,
    _message_name,
    _message_role,
    _select_visible_content,
    _to_output,
)


class TestMessageHelpers:
    """Test message extraction helpers."""

    def test_message_content_from_object(self) -> None:
        """Extract content from object with content attr."""
        msg = MagicMock()
        msg.content = "Hello world"
        assert _message_content(msg) == "Hello world"

    def test_message_content_from_dict(self) -> None:
        """Extract content from dict."""
        msg = {"content": "Hello dict"}
        assert _message_content(msg) == "Hello dict"

    def test_message_content_fallback(self) -> None:
        """Fallback to str for unknown types."""
        assert _message_content("plain string") == "plain string"

    def test_message_role_from_object(self) -> None:
        """Extract role from object with type attr."""
        msg = MagicMock()
        msg.type = "assistant"
        assert _message_role(msg) == "assistant"

    def test_message_role_from_dict(self) -> None:
        """Extract role from dict."""
        msg = {"role": "user"}
        assert _message_role(msg) == "user"

    def test_message_name_from_object(self) -> None:
        """Extract name from object."""
        msg = MagicMock()
        msg.name = "companion"
        assert _message_name(msg) == "companion"

    def test_message_name_from_dict(self) -> None:
        """Extract name from dict."""
        msg = {"name": "researcher"}
        assert _message_name(msg) == "researcher"


class TestUserVisibility:
    """Test user visibility logic."""

    def test_tool_message_not_visible(self) -> None:
        """Tool messages should not be visible."""
        msg = MagicMock()
        msg.type = "tool"
        msg.name = "search"
        assert _is_user_visible(msg) is False

    def test_supervisor_not_visible(self) -> None:
        """Supervisor messages should not be visible."""
        msg = MagicMock()
        msg.type = "assistant"
        msg.name = "supervisor"
        assert _is_user_visible(msg) is False

    def test_assistant_visible(self) -> None:
        """Regular assistant messages should be visible."""
        msg = MagicMock()
        msg.type = "assistant"
        msg.name = "companion"
        assert _is_user_visible(msg) is True

    def test_ai_visible(self) -> None:
        """AI type messages should be visible."""
        msg = MagicMock()
        msg.type = "ai"
        msg.name = "helper"
        assert _is_user_visible(msg) is True


class TestHandoffDetection:
    """Test handoff message detection."""

    def test_transferring_to_is_handoff(self) -> None:
        """'Transferring to X' is a handoff."""
        assert _is_handoff_message("Transferring to companion") is True

    def test_transferring_back_is_handoff(self) -> None:
        """'Transferring back to supervisor' is a handoff."""
        assert _is_handoff_message("Transferring back to supervisor") is True

    def test_handing_off_is_handoff(self) -> None:
        """'Handing off to X' is a handoff."""
        assert _is_handoff_message("Handing off to researcher") is True

    def test_normal_message_not_handoff(self) -> None:
        """Normal messages are not handoffs."""
        assert _is_handoff_message("Hello! How can I help?") is False

    def test_case_insensitive(self) -> None:
        """Handoff detection is case insensitive."""
        assert _is_handoff_message("TRANSFERRING TO AGENT") is True


class TestSelectVisibleContent:
    """Test content selection from message list."""

    def test_selects_last_visible_assistant(self) -> None:
        """Should select last visible assistant message."""
        messages = [
            _make_msg("user", "user", "Hi"),
            _make_msg("ai", "companion", "Hello! I'm here to help."),
            _make_msg("ai", "supervisor", "Transferring back to supervisor"),
        ]
        result = _select_visible_content(messages)
        assert result == "Hello! I'm here to help."

    def test_skips_tool_messages(self) -> None:
        """Should skip tool messages."""
        messages = [
            _make_msg("user", "", "Search for cats"),
            _make_msg("tool", "search", '{"results": ["cat1", "cat2"]}'),
            _make_msg("ai", "researcher", "I found 2 cats!"),
        ]
        result = _select_visible_content(messages)
        assert result == "I found 2 cats!"

    def test_skips_supervisor_handoff(self) -> None:
        """Should skip supervisor handoff messages."""
        messages = [
            _make_msg("user", "", "Hello"),
            _make_msg("ai", "companion", "Hi there! Nice to meet you."),
            _make_msg("ai", "supervisor", "Transferring back to supervisor"),
        ]
        result = _select_visible_content(messages)
        assert result == "Hi there! Nice to meet you."

    def test_fallback_to_any_content(self) -> None:
        """Should fallback to any non-handoff content."""
        messages = [
            _make_msg("ai", "supervisor", "Transferring to companion"),
            _make_msg("ai", "supervisor", "Transferring back to supervisor"),
        ]
        # All are handoffs, but fallback should still try
        result = _select_visible_content(messages)
        # Last message is returned as final fallback
        assert "Transferring" in result

    def test_complex_conversation(self) -> None:
        """Test a realistic multi-turn conversation."""
        messages = [
            _make_msg("user", "", "What is 2+2?"),
            _make_msg("ai", "supervisor", "Transferring to math_expert"),
            _make_msg("tool", "transfer_to_math_expert", ""),
            _make_msg("ai", "math_expert", "2 + 2 equals 4!"),
            _make_msg("ai", "supervisor", "Transferring back to supervisor"),
        ]
        result = _select_visible_content(messages)
        assert result == "2 + 2 equals 4!"


class TestToOutput:
    """Test full output conversion."""

    def test_empty_messages(self) -> None:
        """Empty messages should return empty output."""
        result = _to_output({"messages": []})
        assert result.message == ""

    def test_no_messages_key(self) -> None:
        """Missing messages key should return empty output."""
        result = _to_output({})
        assert result.message == ""

    def test_returns_subagent_response(self) -> None:
        """Should return subagent response, not handoff."""
        result = _to_output(
            {
                "messages": [
                    _make_msg("user", "", "Hi"),
                    _make_msg("ai", "companion", "Hello friend!"),
                    _make_msg("ai", "supervisor", "Transferring back to supervisor"),
                ]
            }
        )
        assert result.message == "Hello friend!"


def _make_msg(role: str, name: str, content: str) -> MagicMock:
    """Create a mock message."""
    msg = MagicMock()
    msg.type = role
    msg.name = name
    msg.content = content
    return msg
