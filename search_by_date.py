#!/usr/bin/env python3
"""
search_by_date.py - Qdrant query for a specific date

Usage:
    python3 search_by_date.py --date 2026-03-06
    python3 search_by_date.py --date 2026-03-06 --sender Laura
"""

import os
import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "openclaw_memory")

def main():
    parser = argparse.ArgumentParser(description="Qdrant search by specific date")
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format (e.g. 2026-03-06)")
    parser.add_argument("--sender", help="Optional: Filter by sender (e.g. 'Laura', 'Alex', or phone number)")
    args = parser.parse_args()

    # Date validation
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date '{args.date}'. Format: YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    target_prefix = args.date + "T"
    filtered_points = []
    
    offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=1000,
            with_payload=True,
            with_vectors=False,
            offset=offset
        )
        
        for point in points:
            payload = point.payload or {}
            timestamp = payload.get('timestamp', '')
            if timestamp.startswith(target_prefix):
                if args.sender:
                    sender = payload.get('sender', '')
                    if args.sender.lower() not in sender.lower():
                        continue
                filtered_points.append(point)
                
        offset = next_offset
        if offset is None:
            break

    if not filtered_points:
        print(f"No entries found for {args.date}.")
        if args.sender:
            print(f"  (Filter: sender contains '{args.sender}')")
        return

    filtered_points.sort(key=lambda p: p.payload.get('timestamp', ''))

    print(f"\n{'='*70}")
    print(f"📅 Entries for {args.date} ({len(filtered_points)} found)")
    if args.sender:
        print(f"👤 Filter: sender contains '{args.sender}'")
    print(f"{'='*70}\n")

    for point in filtered_points:
        payload = point.payload
        timestamp = payload.get('timestamp', 'N/A')
        sender = payload.get('sender', 'unknown')
        text = payload.get('text', '')

        if timestamp != 'N/A':
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = timestamp[11:16] if len(timestamp) > 16 else "N/A"
        else:
            time_str = "N/A"

        print(f"🕐 {time_str} | 👤 {sender}")
        print(f"💬 {text}")
        print("-" * 70)

if __name__ == "__main__":
    main()
