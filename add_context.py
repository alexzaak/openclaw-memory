#!/usr/bin/env python3
import sqlite3
import argparse
from datetime import datetime

DB_PATH = '/home/clawdi/.openclaw/short_term.db'

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
