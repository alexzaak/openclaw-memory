"""
sqlite_service.py – SQLite Service for short_term.db
=====================================================
Schema:
    daily_context: id (PK), timestamp (TEXT), scope (TEXT), content (TEXT)
    learnings:     id (PK), timestamp (TEXT), category (TEXT), source (TEXT),
                   content (TEXT), processed (INTEGER)
"""

import logging
import sqlite3
from contextlib import contextmanager
from config import SQLITE_PATH

log = logging.getLogger("sqlite_service")


@contextmanager
def _get_conn():
    """Context manager for SQLite connections."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ── Daily Context ───────────────────────────────────────────────────────────

def get_daily_context(scope: str | None = None, limit: int = 50) -> list[dict]:
    """Return recent daily_context entries."""
    with _get_conn() as conn:
        try:
            if scope:
                rows = conn.execute(
                    "SELECT id, timestamp, scope, content FROM daily_context "
                    "WHERE scope = ? ORDER BY timestamp DESC LIMIT ?",
                    (scope, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, timestamp, scope, content FROM daily_context "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []


# ── Learnings ───────────────────────────────────────────────────────────────

def get_learnings(
    category: str | None = None,
    processed: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    """Return learnings with optional filters."""
    with _get_conn() as conn:
        try:
            conditions = []
            params = []

            if category:
                conditions.append("category = ?")
                params.append(category)

            if processed is not None:
                conditions.append("processed = ?")
                params.append(1 if processed else 0)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            params.append(limit)

            rows = conn.execute(
                f"SELECT id, timestamp, category, source, content, processed "
                f"FROM learnings {where} ORDER BY timestamp DESC LIMIT ?",
                params,
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.OperationalError:
            return []


def get_learning_categories() -> list[str]:
    """Return distinct learning categories."""
    with _get_conn() as conn:
        try:
            rows = conn.execute(
                "SELECT DISTINCT category FROM learnings ORDER BY category"
            ).fetchall()
            return [row["category"] for row in rows]
        except sqlite3.OperationalError:
            return []
