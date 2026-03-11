#!/usr/bin/env python3
"""
setup_db.py – Initialize the short-term memory SQLite database.

Creates all required tables:
  - daily_context: scoped day-to-day context entries
  - learnings: facts, insights, and observations learned during conversations
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_sqlite_path = os.getenv("SQLITE_PATH", str(Path.home() / ".openclaw" / "short_term.db"))
DB_PATH = os.path.expanduser(_sqlite_path)


def setup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── daily_context ───────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            scope TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_context_scope ON daily_context(scope)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_context_timestamp ON daily_context(timestamp)')

    # ── learnings ───────────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            source TEXT,
            content TEXT NOT NULL,
            processed INTEGER NOT NULL DEFAULT 0
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learnings_timestamp ON learnings(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learnings_processed ON learnings(processed)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category)')

    conn.commit()
    conn.close()
    print(f"✅ Database ready at {DB_PATH}")
    print("   Tables: daily_context, learnings")


if __name__ == '__main__':
    setup()
