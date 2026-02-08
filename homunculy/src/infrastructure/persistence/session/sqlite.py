"""SQLite session store for routing."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from uuid import uuid4

from domain.entities import Session
from domain.interfaces import ChannelInbound, SessionStorePort


@dataclass(frozen=True)
class _Key:
    tenant_id: str
    channel: str
    user_id: str


class SQLiteSessionStore(SessionStorePort):
    """SQLite-backed session store."""

    def __init__(self, db_file: str) -> None:
        self._conn = sqlite3.connect(db_file, check_same_thread=False)
        self._init_schema()

    def get_or_create(self, inbound: ChannelInbound) -> Session:
        """Get or create a session for inbound message."""
        key = self._key(inbound)
        session = self._load(key)
        return session or self._create(key)

    def save(self, session: Session) -> None:
        """Persist updated session."""
        key = self._key_from_session(session)
        if key:
            self._save(key, session)

    def _init_schema(self) -> None:
        """Initialize sessions table."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                tenant_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_json TEXT NOT NULL,
                PRIMARY KEY (tenant_id, channel, user_id)
            )
            """
        )
        self._conn.commit()

    def _load(self, key: _Key) -> Session | None:
        """Load session from SQLite."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT session_json FROM sessions WHERE tenant_id=? AND channel=? AND user_id=?",
            (key.tenant_id, key.channel, key.user_id),
        )
        row = cursor.fetchone()
        return Session(**json.loads(row[0])) if row else None

    def _save(self, key: _Key, session: Session) -> None:
        """Save session to SQLite."""
        payload = json.dumps(session.model_dump(mode="json"))
        self._conn.execute(
            """
            INSERT INTO sessions (tenant_id, channel, user_id, session_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(tenant_id, channel, user_id)
            DO UPDATE SET session_json=excluded.session_json
            """,
            (key.tenant_id, key.channel, key.user_id, payload),
        )
        self._conn.commit()

    def _create(self, key: _Key) -> Session:
        """Create and store a new session."""
        session = self._build_session(key)
        self._save(key, session)
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

    def _key(self, inbound: ChannelInbound) -> _Key:
        """Build lookup key from inbound message."""
        return _Key(inbound.tenant_id, inbound.channel, inbound.user_id)

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
