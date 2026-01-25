"""Unit tests for Session domain entity."""

from domain.entities.session import ConversationState, Session


class TestConversationState:
    """Tests for ConversationState model."""

    def test_create_empty_state(self) -> None:
        state = ConversationState()
        assert state.messages == []
        assert state.current_question == ""
        assert state.documents == []
        assert state.generation == ""

    def test_state_with_messages(self) -> None:
        state = ConversationState(
            messages=[{"role": "user", "content": "Hi"}],
            current_question="What is AI?",
        )
        assert len(state.messages) == 1
        assert state.current_question == "What is AI?"

    def test_state_requires_tool_use(self) -> None:
        state = ConversationState(requires_tool_use=True)
        assert state.requires_tool_use is True


class TestSession:
    """Tests for Session model."""

    def test_create_session(self) -> None:
        session = Session(
            id="s1",
            agent_id="a1",
            thread_id="t1",
        )
        assert session.id == "s1"
        assert session.agent_id == "a1"
        assert session.is_active is True

    def test_session_with_tenant(self) -> None:
        session = Session(
            id="s2",
            agent_id="a1",
            thread_id="t1",
            tenant_id="tenant-123",
        )
        assert session.tenant_id == "tenant-123"

    def test_session_touch(self) -> None:
        session = Session(id="s1", agent_id="a1", thread_id="t1")
        old_updated = session.updated_at
        session.touch()
        assert session.updated_at >= old_updated

    def test_session_close(self) -> None:
        session = Session(id="s1", agent_id="a1", thread_id="t1")
        assert session.is_active is True
        session.close()
        assert session.is_active is False
