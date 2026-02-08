"""SQLite store adapter for portable persistence.

Extends LangGraph BaseStore for InjectedStore compatibility.
File-based storage with WAL mode for concurrent access.
"""

import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
)

from common.logger import get_logger

logger = get_logger(__name__)


class SQLiteStoreAdapter(BaseStore):
    """SQLite BaseStore with WAL mode and namespace prefix search."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = _create_connection(db_path)
        _initialize_schema(self._conn)
        logger.info("SQLiteStore initialized", path=db_path)

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Dispatch operations synchronously."""
        return [_dispatch(self._conn, op) for op in ops]

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Dispatch operations asynchronously (wraps sync)."""
        return self.batch(ops)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()

    def __enter__(self) -> "SQLiteStoreAdapter":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# --- Op dispatching ---


def _dispatch(conn: sqlite3.Connection, op: Op) -> Result:
    """Route operation to handler."""
    if isinstance(op, GetOp):
        return _handle_get(conn, op)
    if isinstance(op, SearchOp):
        return _handle_search(conn, op)
    if isinstance(op, PutOp):
        return _handle_put(conn, op)
    if isinstance(op, ListNamespacesOp):
        return _handle_list(conn, op)
    msg = f"Unknown op type: {type(op)}"
    raise ValueError(msg)


def _handle_get(conn: sqlite3.Connection, op: GetOp) -> Item | None:
    """Get item by namespace + key."""
    row = conn.execute(
        "SELECT * FROM store WHERE namespace=? AND key=?",
        (_ns(op.namespace), op.key),
    ).fetchone()
    return _row_to_item(row, op.namespace) if row else None


def _handle_search(
    conn: sqlite3.Connection,
    op: SearchOp,
) -> list[SearchItem]:
    """Search with namespace prefix matching."""
    prefix = _ns(op.namespace_prefix)
    rows = conn.execute(
        "SELECT * FROM store WHERE namespace LIKE ? LIMIT ? OFFSET ?",
        (f"{prefix}%", op.limit, op.offset),
    ).fetchall()
    items = [_to_search_item(r) for r in rows]
    return _apply_filter(items, op.filter)


def _handle_put(conn: sqlite3.Connection, op: PutOp) -> None:
    """Thread-safe put using immediate transactions."""
    ns = _ns(op.namespace)
    conn.execute("BEGIN IMMEDIATE")
    try:
        if op.value is None:
            conn.execute(
                "DELETE FROM store WHERE namespace=? AND key=?",
                (ns, op.key),
            )
        else:
            _upsert(conn, ns, op.key, op.value)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _handle_list(
    conn: sqlite3.Connection,
    op: ListNamespacesOp,
) -> list[tuple[str, ...]]:
    """List distinct namespaces."""
    rows = conn.execute(
        "SELECT DISTINCT namespace FROM store LIMIT ? OFFSET ?",
        (op.limit, op.offset),
    ).fetchall()
    namespaces = [_parse_ns(r["namespace"]) for r in rows]
    return _filter_namespaces(namespaces, op)


# --- SQL helpers ---


def _upsert(
    conn: sqlite3.Connection,
    ns: str,
    key: str,
    value: dict,
) -> None:
    """Insert or update item."""
    now = datetime.now().isoformat()
    val = json.dumps(value)
    existing = conn.execute(
        "SELECT created_at FROM store WHERE namespace=? AND key=?",
        (ns, key),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE store SET value=?, updated_at=? WHERE namespace=? AND key=?",
            (val, now, ns, key),
        )
    else:
        conn.execute(
            "INSERT INTO store (namespace,key,value,created_at,updated_at) VALUES (?,?,?,?,?)",
            (ns, key, val, now, now),
        )


# --- Conversion helpers ---


def _ns(namespace: tuple[str, ...]) -> str:
    """Serialize namespace tuple."""
    return "|".join(namespace)


def _parse_ns(ns_str: str) -> tuple[str, ...]:
    """Deserialize namespace string."""
    return tuple(ns_str.split("|"))


def _row_to_item(row: sqlite3.Row, namespace: tuple[str, ...]) -> Item:
    """Convert row to LangGraph Item."""
    return Item(
        value=json.loads(row["value"]),
        key=row["key"],
        namespace=namespace,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _to_search_item(row: sqlite3.Row) -> SearchItem:
    """Convert row to SearchItem with parsed namespace."""
    ns = _parse_ns(row["namespace"])
    return SearchItem(
        value=json.loads(row["value"]),
        key=row["key"],
        namespace=ns,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        score=0.0,
    )


def _apply_filter(
    items: list[SearchItem],
    filter_dict: dict[str, Any] | None,
) -> list[SearchItem]:
    """Apply key-value filter on items."""
    if not filter_dict:
        return items
    return [i for i in items if _matches(i, filter_dict)]


def _matches(item: SearchItem, criteria: dict[str, Any]) -> bool:
    """Check item value matches all criteria."""
    return all(item.value.get(k) == v for k, v in criteria.items())


def _filter_namespaces(
    namespaces: list[tuple[str, ...]],
    op: ListNamespacesOp,
) -> list[tuple[str, ...]]:
    """Apply match conditions and depth filter."""
    result = namespaces
    if op.max_depth is not None:
        result = [ns for ns in result if len(ns) <= op.max_depth]
    return result


# --- Setup helpers ---


def _create_connection(db_path: str) -> sqlite3.Connection:
    """Create SQLite connection with multi-user timeout."""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _initialize_schema(conn: sqlite3.Connection) -> None:
    """Optimize SQLite for multi-user AI workloads."""
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA mmap_size=30000000000;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS store (
            namespace TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (namespace, key)
        )
    """)
    conn.commit()
