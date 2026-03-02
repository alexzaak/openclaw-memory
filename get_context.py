#!/usr/bin/env python3
import sqlite3
import argparse
from datetime import datetime, timedelta

DB_PATH = '/home/clawdi/.openclaw/short_term.db'

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
        print(f"Keine neuen Einträge im Kurzzeitgedächtnis für {args.scope.upper()}.")
        return

    print(f"--- 🧠 Kurzzeitgedächtnis (Letzte {args.hours}h) für {args.scope.upper()} ---")
    for row in rows:
        ts = row[0][:16].replace('T', ' ')
        print(f"[{ts}] [{row[1].upper()}]: {row[2]}")

if __name__ == '__main__':
    main()
