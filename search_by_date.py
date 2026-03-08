#!/usr/bin/env python3
"""
search_by_date.py - Qdrant-Abfrage für ein spezifisches Datum

Nutzung:
    python3 search_by_date.py --date 2026-03-06
    python3 search_by_date.py --date 2026-03-06 --sender Laura
"""

import argparse
import sys
from datetime import datetime
from qdrant_client import QdrantClient

def main():
    parser = argparse.ArgumentParser(description="Qdrant-Suche nach spezifischem Datum")
    parser.add_argument("--date", required=True, help="Datum im Format YYYY-MM-DD (z.B. 2026-03-06)")
    parser.add_argument("--sender", help="Optional: Nach Sender filtern (z.B. 'Laura', 'Alex', oder Telefonnummer)")
    args = parser.parse_args()

    # Validierung des Datums
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print(f"Fehler: Ungültiges Datum '{args.date}'. Format: YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    client = QdrantClient(host="127.0.0.1", port=6333)

    target_prefix = args.date + "T"
    filtered_points = []
    
    offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name="openclaw_memory",
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
        print(f"Keine Einträge für {args.date} gefunden.")
        if args.sender:
            print(f"  (Filter: Sender enthält '{args.sender}')")
        return

    filtered_points.sort(key=lambda p: p.payload.get('timestamp', ''))

    print(f"\n{'='*70}")
    print(f"📅 Einträge für {args.date} ({len(filtered_points)} gefunden)")
    if args.sender:
        print(f"👤 Filter: Sender enthält '{args.sender}'")
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
