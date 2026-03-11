#!/usr/bin/env python3
"""
get_learnings.py – Retrieve learnings from short-term memory.

Usage:
    python3 short_term_memory/get_learnings.py                    # All unprocessed
    python3 short_term_memory/get_learnings.py --all              # All (incl. processed)
    python3 short_term_memory/get_learnings.py --category fact    # Filter by category
    python3 short_term_memory/get_learnings.py --hours 24         # Last 24h only
"""

import os
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_sqlite_path = os.getenv("SQLITE_PATH", str(Path.home() / ".openclaw" / "short_term.db"))
DB_PATH = os.path.expanduser(_sqlite_path)


def main():
    parser = argparse.ArgumentParser(description="Retrieve learnings from short-term memory.")
    parser.add_argument("--all", action="store_true", help="Include already-processed learnings")
    parser.add_argument("--category", default=None, help="Filter by category")
    parser.add_argument("--hours", type=int, default=None, help="Only show learnings from last N hours")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    conditions = []
    params = []

    if not args.all:
        conditions.append("processed = 0")

    if args.category:
        conditions.append("category = ?")
        params.append(args.category)

    if args.hours:
        cutoff = (datetime.now() - timedelta(hours=args.hours)).isoformat()
        conditions.append("timestamp >= ?")
        params.append(cutoff)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT id, timestamp, category, source, content, processed FROM learnings {where} ORDER BY timestamp ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if args.json:
        import json
        data = [
            {"id": r[0], "time": r[1], "category": r[2], "source": r[3], "content": r[4], "processed": bool(r[5])}
            for r in rows
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not rows:
        label = "learnings" if args.all else "unprocessed learnings"
        print(f"No {label} found.")
        return

    status = "all" if args.all else "unprocessed"
    print(f"--- 📚 Learnings ({status}, {len(rows)} found) ---")
    for r in rows:
        ts = r[1][:16].replace('T', ' ')
        cat = r[2]
        source = f" ← {r[3]}" if r[3] else ""
        flag = " ✓" if r[5] else ""
        print(f"[{ts}] [{cat}]{flag}: {r[4]}{source}")


if __name__ == '__main__':
    main()
