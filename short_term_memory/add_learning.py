#!/usr/bin/env python3
"""
add_learning.py – Record a learning/insight into short-term memory.

Usage:
    python3 short_term_memory/add_learning.py --text "Laura prefers almond milk"
    python3 short_term_memory/add_learning.py --text "Qdrant needs restart after OOM" --category system
    python3 short_term_memory/add_learning.py --text "Alex dislikes surprises" --source "conversation with Laura"
"""

import os
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_sqlite_path = os.getenv("SQLITE_PATH", str(Path.home() / ".openclaw" / "short_term.db"))
DB_PATH = os.path.expanduser(_sqlite_path)


def main():
    parser = argparse.ArgumentParser(description="Add a learning to short-term memory.")
    parser.add_argument("--text", required=True, help="The learning/insight to store")
    parser.add_argument("--category", default="general",
                        help="Category (e.g. general, preference, fact, system)")
    parser.add_argument("--source", default=None,
                        help="Optional: where this learning came from")
    args = parser.parse_args()

    timestamp = datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO learnings (timestamp, category, source, content) VALUES (?, ?, ?, ?)",
        (timestamp, args.category, args.source, args.text)
    )
    conn.commit()
    conn.close()

    src = f" (source: {args.source})" if args.source else ""
    print(f"✅ [{timestamp[:16].replace('T', ' ')}] Learning added [{args.category}]: {args.text}{src}")


if __name__ == '__main__':
    main()
