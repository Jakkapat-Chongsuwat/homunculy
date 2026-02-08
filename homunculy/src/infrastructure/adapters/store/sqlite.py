"""SQLite store adapter for portable persistence.

File-based storage that works on Windows and Linux.
Uses SQLite for cross-platform compatibility.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from common.logger import get_logger
from domain.interfaces.store import StoreItem, StorePort, StoreQuery

logger = get_logger(__name__)


class SQLiteStoreAdapter(StorePort):
    """SQLite implementation of StorePort."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = self._create_connection()
        self._initialize_schema()
        logger.info("SQLiteStore initialized", path=db_path)

    def _create_connection(self) -> sqlite3.Connection:
        """Create SQLite connection."""
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        """Create tables if not exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS store (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (namespace, key)
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_namespace
            ON store(namespace)
        """)
        self._conn.commit()

    async def put(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict,
    ) -> None:
        """Store value at namespace+key."""
        ns_str = _serialize_namespace(namespace)
        value_str = json.dumps(value)
        now = datetime.now().isoformat()

        existing = self._conn.execute(
            "SELECT created_at FROM store WHERE namespace=? AND key=?",
            (ns_str, key),
        ).fetchone()

        if existing:
            self._conn.execute(
                """UPDATE store
                   SET value=?, updated_at=?
                   WHERE namespace=? AND key=?""",
                (value_str, now, ns_str, key),
            )
        else:
            self._conn.execute(
                """INSERT INTO store
                   (namespace, key, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (ns_str, key, value_str, now, now),
            )
        self._conn.commit()

    async def get(
        self,
        namespace: tuple[str, ...],
        key: str,
    ) -> StoreItem | None:
        """Get value by namespace+key."""
        ns_str = _serialize_namespace(namespace)
        row = self._conn.execute(
            "SELECT * FROM store WHERE namespace=? AND key=?",
            (ns_str, key),
        ).fetchone()

        if not row:
            return None
        return _row_to_item(row, namespace)

    async def search(self, query: StoreQuery) -> list[StoreItem]:
        """Search items in namespace."""
        ns_str = _serialize_namespace(query.namespace)
        rows = self._conn.execute(
            "SELECT * FROM store WHERE namespace=? LIMIT ?",
            (ns_str, query.limit),
        ).fetchall()

        items = [_row_to_item(r, query.namespace) for r in rows]
        if query.filter_dict:
            items = _filter_items(items, query.filter_dict)
        return items[: query.limit]

    async def delete(
        self,
        namespace: tuple[str, ...],
        key: str,
    ) -> bool:
        """Delete item by namespace+key."""
        ns_str = _serialize_namespace(namespace)
        cursor = self._conn.execute(
            "DELETE FROM store WHERE namespace=? AND key=?",
            (ns_str, key),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()


def _serialize_namespace(namespace: tuple[str, ...]) -> str:
    """Serialize namespace tuple to string."""
    return "|".join(namespace)


def _row_to_item(row: sqlite3.Row, namespace: tuple) -> StoreItem:
    """Convert SQLite row to StoreItem."""
    return StoreItem(
        namespace=namespace,
        key=row["key"],
        value=json.loads(row["value"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _filter_items(items: list[StoreItem], filter_dict: dict) -> list[StoreItem]:
    """Filter items by criteria."""
    return [i for i in items if _matches_filter(i, filter_dict)]


def _matches_filter(item: StoreItem, filter_dict: dict) -> bool:
    """Check if item matches filter."""
    for key, val in filter_dict.items():
        if item.value.get(key) != val:
            return False
    return True
