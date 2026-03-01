#!/usr/bin/env python3
"""
seed_sqlite.py – Erstellt short_term.db mit Schema und Demodaten
=================================================================
Schema (wie vom User definiert):
    logs:  id (PK), timestamp (DATETIME), category (TEXT), content (TEXT), mood_score (INTEGER)
    state: key (TEXT PK), value (TEXT), updated_at (DATETIME)
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".openclaw" / "short_term.db"


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
        (now - timedelta(hours=2), "LRN", "Gelernt: FalkorDB Cypher MERGE vs CREATE – MERGE ist idempotent.", 8),
        (now - timedelta(hours=5), "LRN", "Erkenntnis: Bei Qdrant scroll() muss order_by auf indexed fields zeigen.", 7),
        (now - timedelta(days=1, hours=3), "LRN", "Pattern: Async Context Manager für DB-Pool-Lifecycle in FastAPI.", 9),
        (now - timedelta(days=1, hours=8), "LRN", "Fehler vermieden: UUID5 statt UUID4 für deterministische Point-IDs.", 8),
        (now - timedelta(days=2), "LRN", "Gelernt: Podman network_mode host vs bridge – host ist für lokale DBs besser.", 6),

        # TEMP – Temperature readings (Konsti's Fieberwerte)
        (now - timedelta(hours=1), "TEMP", "Konsti: 37.2°C", 5),
        (now - timedelta(hours=4), "TEMP", "Konsti: 37.8°C", 4),
        (now - timedelta(hours=8), "TEMP", "Konsti: 38.1°C", 3),
        (now - timedelta(hours=12), "TEMP", "Konsti: 38.5°C", 3),
        (now - timedelta(hours=16), "TEMP", "Konsti: 38.3°C", 3),
        (now - timedelta(hours=20), "TEMP", "Konsti: 37.9°C", 4),
        (now - timedelta(days=1), "TEMP", "Konsti: 37.4°C", 5),
        (now - timedelta(days=1, hours=8), "TEMP", "Konsti: 37.1°C", 6),

        # SYS – System status
        (now - timedelta(minutes=30), "SYS", "Memory Watcher läuft stabil. 42 Einträge heute verarbeitet.", 7),
        (now - timedelta(hours=6), "SYS", "Qdrant Disk Usage: 2.1 GB / 50 GB", 6),
        (now - timedelta(days=1), "SYS", "REM-Schlaf-Job: 3 neue Fakten in Graph extrahiert.", 8),

        # MOOD – General mood tracking
        (now - timedelta(hours=1), "MOOD", "Guter Tag – Konsti geht es besser, Projekt läuft.", 8),
        (now - timedelta(days=1), "MOOD", "Etwas gestresst – Konsti hat Fieber, viel zu tun.", 4),
        (now - timedelta(days=2), "MOOD", "Produktiver Tag, viel geschafft am Dashboard-Projekt.", 9),
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
