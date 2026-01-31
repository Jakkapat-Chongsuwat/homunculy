"""Session store for channel routing (in-memory)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from domain.entities import Session
from domain.interfaces import ChannelInbound, SessionStorePort


@dataclass(frozen=True)
class _Key:
    tenant_id: str
    channel: str
    user_id: str


class InMemorySessionStore(SessionStorePort):
    """In-memory session store for routing."""

    def __init__(self) -> None:
        self._by_key: dict[_Key, Session] = {}

    def get_or_create(self, inbound: ChannelInbound) -> Session:
        """Get or create a session for inbound message."""
        key = self._key(inbound)
        return self._by_key.get(key) or self._create(key)

    def save(self, session: Session) -> None:
        """Persist updated session."""
        key = self._key_from_session(session)
        if key:
            self._by_key[key] = session

    def _key(self, inbound: ChannelInbound) -> _Key:
        """Build lookup key from inbound message."""
        return _Key(inbound.tenant_id, inbound.channel, inbound.user_id)

    def _create(self, key: _Key) -> Session:
        """Create and store a new session."""
        session = self._build_session(key)
        self._by_key[key] = session
        return session

    def _build_session(self, key: _Key) -> Session:
        """Build a new session entity."""
        return Session(
            id=self._new_id(),
            agent_id="default",
            thread_id=self._new_id(),
            tenant_id=key.tenant_id,
            metadata=self._metadata(key),
        )

    def _metadata(self, key: _Key) -> dict:
        """Build session metadata."""
        return {"channel": key.channel, "user_id": key.user_id}

    def _key_from_session(self, session: Session) -> _Key | None:
        """Build lookup key from session metadata."""
        channel = session.metadata.get("channel")
        user_id = session.metadata.get("user_id")
        if not (session.tenant_id and channel and user_id):
            return None
        return _Key(session.tenant_id, channel, user_id)

    def _new_id(self) -> str:
        """Generate a new session id."""
        return uuid4().hex
