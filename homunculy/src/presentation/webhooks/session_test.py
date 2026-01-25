"""Unit tests for Session webhook handler."""

from domain.entities.session import Session


class TestSessionWebhook:
    """Tests for session webhook handling."""

    def test_session_creation(self) -> None:
        session = Session(
            id="s1",
            agent_id="a1",
            thread_id="t1",
        )
        assert session.id == "s1"
        assert session.is_active is True

    def test_session_close(self) -> None:
        session = Session(
            id="s1",
            agent_id="a1",
            thread_id="t1",
        )
        session.close()
        assert session.is_active is False

    def test_session_with_tenant(self) -> None:
        session = Session(
            id="s1",
            agent_id="a1",
            thread_id="t1",
            tenant_id="tenant-123",
        )
        assert session.tenant_id == "tenant-123"

    def test_session_metadata(self) -> None:
        session = Session(
            id="s1",
            agent_id="a1",
            thread_id="t1",
            metadata={"key": "value"},
        )
        assert session.metadata == {"key": "value"}
