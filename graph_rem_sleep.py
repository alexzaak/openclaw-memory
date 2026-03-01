#!/usr/bin/env python3
import sys
import os
import json
import requests
from datetime import datetime, date
from qdrant_client import QdrantClient
from falkordb import FalkorDB

# --- Konfiguration ---
QDRANT_URL = "http://127.0.0.1:6333"
FALKOR_HOST = "127.0.0.1"
FALKOR_PORT = 6379
GRAPH_NAME = "openclaw_ontology"
EMBED_MODEL = "nomic-embed-text"
OLLAMA_URL = "http://127.0.0.1:11434"

# Hier bräuchte das Script einen API-Key für die finale Analyse.
# Wir können es aber so bauen, dass es die Cypher-Queries vom Agenten bekommt
# oder selbst via Google API anfragt.

def get_today_chats(target_date=None):
    if not target_date:
        target_date = date.today().isoformat()
    
    client = QdrantClient(host="127.0.0.1", port=6333)
    
    # Wir holen uns eine größere Menge an Punkten und filtern lokal nach Datum im Payload
    # (In einer finalen Version nutzen wir Qdrant Filter-Indizes)
    results = client.scroll(
        collection_name="openclaw_memory",
        limit=100,
        with_payload=True,
        with_vectors=False
    )[0]
    
    daily_text = []
    for res in results:
        ts = res.payload.get("timestamp", "")
        if ts.startswith(target_date):
            sender = res.payload.get("sender", "unknown")
            text = res.payload.get("text", "")
            daily_text.append(f"[ {sender} ]: {text}")
    
    return "\n".join(daily_text)

def run_cypher_batch(queries):
    db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
    graph = db.select_graph(GRAPH_NAME)
    
    results = []
    for q in queries:
        if q.strip():
            try:
                graph.query(q)
                results.append(True)
            except Exception as e:
                print(f"Fehler bei Query {q}: {e}")
                results.append(False)
    return results

if __name__ == "__main__":
    # Wenn das Script mit 'extract' aufgerufen wird, gibt es die heutigen Chats aus
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        print(get_today_chats())
    
    # Wenn es mit 'ingest' aufgerufen wird, erwartet es Cypher-Queries via stdin
    elif len(sys.argv) > 1 and sys.argv[1] == "ingest":
        input_data = sys.stdin.read()
        try:
            queries = json.loads(input_data)
            run_cypher_batch(queries)
            print("Ingestion erfolgreich")
        except Exception as e:
            print(f"Fehler beim Parsen der Queries: {e}")
