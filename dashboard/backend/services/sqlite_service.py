"""
sqlite_service.py – SQLite Service for short_term.db
=====================================================
Schema:
    logs:  id (PK), timestamp (DATETIME), category (TEXT), content (TEXT), mood_score (INTEGER)
    state: key (TEXT PK), value (TEXT), updated_at (DATETIME)
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


def get_logs(
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Get logs, optionally filtered by category."""
    with _get_conn() as conn:
        if category:
            rows = conn.execute(
                "SELECT * FROM logs WHERE category = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (category, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]


def get_log_categories() -> list[str]:
    """Return distinct log categories."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM logs ORDER BY category"
        ).fetchall()
        return [row["category"] for row in rows]


def get_state() -> dict:
    """Return all current state key-value pairs."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT key, value, updated_at FROM state ORDER BY key"
        ).fetchall()
        return {row["key"]: {"value": row["value"], "updated_at": row["updated_at"]} for row in rows}


def get_state_value(key: str) -> dict | None:
    """Return a single state value."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT key, value, updated_at FROM state WHERE key = ?", (key,)
        ).fetchone()
        return dict(row) if row else None


def get_mood_timeline(days: int = 7) -> list[dict]:
    """Return mood_score time-series for the last N days."""
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT timestamp, mood_score
            FROM logs
            WHERE mood_score IS NOT NULL
              AND timestamp >= datetime('now', ?)
            ORDER BY timestamp ASC
            """,
            (f"-{days} days",),
        ).fetchall()
        return [dict(row) for row in rows]


def get_learning_log(limit: int = 20) -> list[dict]:
    """Return the latest LRN (learning / self-improvement) entries."""
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp, content, mood_score
            FROM logs
            WHERE category = 'LRN'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
