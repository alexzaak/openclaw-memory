#!/usr/bin/env python3
import sys
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, date
from qdrant_client import QdrantClient
from falkordb import FalkorDB

# --- Configuration (loaded from .env) ---
load_dotenv()

_qdrant_host = os.getenv("QDRANT_HOST", "127.0.0.1")
_qdrant_port = os.getenv("QDRANT_PORT", "6333")
QDRANT_URL = f"http://{_qdrant_host}:{_qdrant_port}"
FALKOR_HOST = os.getenv("FALKOR_HOST", "127.0.0.1")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))
GRAPH_NAME = os.getenv("FALKOR_GRAPH", "openclaw_ontology")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

# This script would need an API key for the final analysis.
# We can build it so that it receives Cypher queries from the agent
# or queries the Google API itself.

def get_today_chats(target_date=None):
    if not target_date:
        target_date = date.today().isoformat()
    
    client = QdrantClient(host="127.0.0.1", port=6333)
    
    # Fetch a larger set of points and filter locally by date in the payload
    # (In a final version we would use Qdrant filter indices)
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
                print(f"Error in query {q}: {e}")
                results.append(False)
    return results

if __name__ == "__main__":
    # If called with 'extract', output today's chats
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        print(get_today_chats())
    
    # If called with 'ingest', expect Cypher queries via stdin
    elif len(sys.argv) > 1 and sys.argv[1] == "ingest":
        input_data = sys.stdin.read()
        try:
            queries = json.loads(input_data)
            run_cypher_batch(queries)
            print("Ingestion successful")
        except Exception as e:
            print(f"Error parsing queries: {e}")
