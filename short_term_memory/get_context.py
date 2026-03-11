#!/usr/bin/env python3
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
    parser = argparse.ArgumentParser(description="Get short-term memory context.")
    parser.add_argument("--scope", required=True, help="Primary scope (e.g., alex or laura)")
    parser.add_argument("--hours", type=int, default=48, help="Hours to look back")
    args = parser.parse_args()

    cutoff_time = (datetime.now() - timedelta(hours=args.hours)).isoformat()
    scopes = [args.scope.lower(), 'family', 'system']
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    placeholders = ','.join(['?'] * len(scopes))
    query = f"""
        SELECT timestamp, scope, content 
        FROM daily_context 
        WHERE timestamp >= ? AND scope IN ({placeholders})
        ORDER BY timestamp ASC
    """
    
    cursor.execute(query, [cutoff_time] + scopes)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"No new entries in short-term memory for {args.scope.upper()}.")
        return

    print(f"--- 🧠 Short-term memory (last {args.hours}h) for {args.scope.upper()} ---")
    for row in rows:
        ts = row[0][:16].replace('T', ' ')
        print(f"[{ts}] [{row[1].upper()}]: {row[2]}")

if __name__ == '__main__':
    main()
