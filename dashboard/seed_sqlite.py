#!/usr/bin/env python3
"""
seed_sqlite.py – Creates short_term.db with schema and demo data
=================================================================
Schema (as defined by user):
    logs:  id (PK), timestamp (DATETIME), category (TEXT), content (TEXT), mood_score (INTEGER)
    state: key (TEXT PK), value (TEXT), updated_at (DATETIME)
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

_sqlite_path = os.getenv("SQLITE_PATH", str(Path.home() / ".openclaw" / "short_term.db"))
DB_PATH = Path(os.path.expanduser(_sqlite_path))


def seed():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    # Schema
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   DATETIME NOT NULL DEFAULT (datetime('now')),
            category    TEXT NOT NULL,
            content     TEXT NOT NULL,
            mood_score  INTEGER
        );

        CREATE TABLE IF NOT EXISTS state (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            updated_at  DATETIME NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_logs_category ON logs(category);
        CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
    """)

    # Seed data — only insert if tables are empty
    existing = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    if existing > 0:
        print(f"Database already has {existing} log entries – skipping seed data.")
        conn.close()
        return

    now = datetime.now()
    logs = [
        # LRN – Learning / Self-improvement entries
        (now - timedelta(hours=2), "LRN", "Learned: FalkorDB Cypher MERGE vs CREATE – MERGE is idempotent.", 8),
        (now - timedelta(hours=5), "LRN", "Insight: Qdrant scroll() order_by must point to indexed fields.", 7),
        (now - timedelta(days=1, hours=3), "LRN", "Pattern: Async Context Manager for DB pool lifecycle in FastAPI.", 9),
        (now - timedelta(days=1, hours=8), "LRN", "Bug avoided: UUID5 instead of UUID4 for deterministic point IDs.", 8),
        (now - timedelta(days=2), "LRN", "Learned: Podman network_mode host vs bridge – host is better for local DBs.", 6),

        # TEMP – Temperature readings (Konsti's fever readings)
        (now - timedelta(hours=1), "TEMP", "Konsti: 37.2°C", 5),
        (now - timedelta(hours=4), "TEMP", "Konsti: 37.8°C", 4),
        (now - timedelta(hours=8), "TEMP", "Konsti: 38.1°C", 3),
        (now - timedelta(hours=12), "TEMP", "Konsti: 38.5°C", 3),
        (now - timedelta(hours=16), "TEMP", "Konsti: 38.3°C", 3),
        (now - timedelta(hours=20), "TEMP", "Konsti: 37.9°C", 4),
        (now - timedelta(days=1), "TEMP", "Konsti: 37.4°C", 5),
        (now - timedelta(days=1, hours=8), "TEMP", "Konsti: 37.1°C", 6),

        # SYS – System status
        (now - timedelta(minutes=30), "SYS", "Memory Watcher running stable. 42 entries processed today.", 7),
        (now - timedelta(hours=6), "SYS", "Qdrant Disk Usage: 2.1 GB / 50 GB", 6),
        (now - timedelta(days=1), "SYS", "REM sleep job: 3 new facts extracted into graph.", 8),

        # MOOD – General mood tracking
        (now - timedelta(hours=1), "MOOD", "Good day – Konsti is doing better, project is on track.", 8),
        (now - timedelta(days=1), "MOOD", "A bit stressed – Konsti has a fever, lots to do.", 4),
        (now - timedelta(days=2), "MOOD", "Productive day, got a lot done on the dashboard project.", 9),
    ]

    conn.executemany(
        "INSERT INTO logs (timestamp, category, content, mood_score) VALUES (?, ?, ?, ?)",
        [(ts.isoformat(), cat, content, mood) for ts, cat, content, mood in logs],
    )

    # State entries
    states = [
        ("konsti_temperature", "37.2", now.isoformat()),
        ("system_status", "healthy", now.isoformat()),
        ("watcher_running", "true", now.isoformat()),
        ("qdrant_points_count", "1247", now.isoformat()),
        ("last_rem_sleep", (now - timedelta(hours=8)).isoformat(), now.isoformat()),
        ("graph_node_count", "34", now.isoformat()),
        ("graph_edge_count", "67", now.isoformat()),
    ]

    conn.executemany(
        "INSERT OR REPLACE INTO state (key, value, updated_at) VALUES (?, ?, ?)",
        states,
    )

    conn.commit()
    conn.close()
    print(f"✅ Database seeded: {DB_PATH}")
    print(f"   {len(logs)} log entries, {len(states)} state entries")


if __name__ == "__main__":
    seed()
