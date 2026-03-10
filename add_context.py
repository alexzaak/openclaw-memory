#!/usr/bin/env python3
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
    parser = argparse.ArgumentParser(description="Add entry to short-term memory.")
    parser.add_argument("--scope", required=True, choices=['alex', 'laura', 'family', 'system'], help="Target scope")
    parser.add_argument("--text", required=True, help="Content to remember")
    args = parser.parse_args()

    timestamp = datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO daily_context (timestamp, scope, content) VALUES (?, ?, ?)",
        (timestamp, args.scope, args.text)
    )
    conn.commit()
    conn.close()
    print(f"✅ [{timestamp[:16].replace('T', ' ')}] Context added to '{args.scope.upper()}': {args.text}")

if __name__ == '__main__':
    main()
