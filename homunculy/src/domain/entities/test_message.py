"""Unit tests for Message domain entity."""

from domain.entities.message import Message, MessageRole


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_user_role(self) -> None:
        assert MessageRole.USER.value == "user"

    def test_assistant_role(self) -> None:
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_system_role(self) -> None:
        assert MessageRole.SYSTEM.value == "system"

    def test_tool_role(self) -> None:
        assert MessageRole.TOOL.value == "tool"


class TestMessage:
    """Tests for Message model."""

    def test_create_message(self) -> None:
        msg = Message(
            id="m1",
            role=MessageRole.USER,
            content="Hello",
            thread_id="t1",
        )
        assert msg.id == "m1"
        assert msg.content == "Hello"

    def test_is_user(self) -> None:
        msg = Message(
            id="m1",
            role=MessageRole.USER,
            content="Hi",
            thread_id="t1",
        )
        assert msg.is_user() is True
        assert msg.is_assistant() is False

    def test_is_assistant(self) -> None:
        msg = Message(
            id="m2",
            role=MessageRole.ASSISTANT,
            content="Hello!",
            thread_id="t1",
        )
        assert msg.is_assistant() is True
        assert msg.is_user() is False

    def test_message_with_metadata(self) -> None:
        msg = Message(
            id="m3",
            role=MessageRole.SYSTEM,
            content="System prompt",
            thread_id="t1",
            metadata={"priority": "high"},
        )
        assert msg.metadata == {"priority": "high"}
