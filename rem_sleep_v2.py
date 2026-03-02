#!/usr/bin/env python3
import sys
import os
import json
import sqlite3
from datetime import datetime, date, timedelta
from falkordb import FalkorDB

DB_PATH = '/home/clawdi/.openclaw/short_term.db'
FALKOR_HOST = "127.0.0.1"
FALKOR_PORT = 6379
GRAPH_NAME = "openclaw_ontology"

def extract_daily_context():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hole alle Kontext-Einträge
    cursor.execute("SELECT id, timestamp, scope, content FROM daily_context ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    
    # Hole alle Learnings aus den logs
    cursor.execute("SELECT id, timestamp, category, content FROM logs WHERE category = 'LRN' ORDER BY timestamp ASC")
    lrn_rows = cursor.fetchall()
    
    conn.close()
    
    output = {
        "context": {},
        "learnings": [{"id": r[0], "time": r[1], "content": r[3]} for r in lrn_rows]
    }
    
    for r in rows:
        scope = r[2]
        if scope not in output["context"]:
            output["context"][scope] = []
        output["context"][scope].append({"id": r[0], "time": r[1], "content": r[3]})
        
    print(json.dumps(output, indent=2))

def compress_context(summary_json_str):
    try:
        summaries = json.loads(summary_json_str)
    except Exception as e:
        print(f"Fehler beim Parsen der Summaries (JSON erwartet): {e}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Lösche alte Kontext-Einträge
    cursor.execute("DELETE FROM daily_context")
    
    # Füge die komprimierten Zusammenfassungen als EINEN neuen Eintrag pro Scope ein
    # Wir setzen den Zeitstempel auf 23:59 des aktuellen/gestrigen Tages
    summary_time = datetime.now().replace(hour=23, minute=59, second=59).isoformat()
    
    for scope, text in summaries.items():
        if text.strip():
            cursor.execute(
                "INSERT INTO daily_context (timestamp, scope, content) VALUES (?, ?, ?)",
                (summary_time, scope, f"Zusammenfassung: {text}")
            )
    
    # (Optional) LRN Logs als verarbeitet markieren oder löschen, 
    # belassen wir vorerst fürs Dashboard.
    
    conn.commit()
    conn.close()
    print("✅ Kurzzeitgedächtnis erfolgreich komprimiert und bereinigt.")

def ingest_graph(cypher_json_str):
    try:
        queries = json.loads(cypher_json_str)
    except Exception as e:
        print(f"Fehler beim Parsen der Cypher Queries (JSON Array erwartet): {e}")
        sys.exit(1)
        
    db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
    graph = db.select_graph(GRAPH_NAME)
    
    success_count = 0
    for q in queries:
        if q.strip():
            try:
                graph.query(q)
                success_count += 1
            except Exception as e:
                print(f"Fehler bei Query '{q}': {e}")
                
    print(f"✅ {success_count}/{len(queries)} Cypher Queries erfolgreich in FalkorDB überführt.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: rem_sleep_v2.py <extract|compress|ingest> [json_data]")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "extract":
        extract_daily_context()
    elif action == "compress":
        if len(sys.argv) < 3:
            print("Fehler: JSON String für 'compress' erwartet.")
            sys.exit(1)
        compress_context(sys.argv[2])
    elif action == "ingest":
        if len(sys.argv) < 3:
            print("Fehler: JSON String für 'ingest' erwartet.")
            sys.exit(1)
        ingest_graph(sys.argv[2])
    else:
        print(f"Unbekannte Aktion: {action}")
