#!/usr/bin/env python3
import sys
import os
import json
import sqlite3
import subprocess
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

_sqlite_path = os.getenv("SQLITE_PATH", str(Path.home() / ".openclaw" / "short_term.db"))
DB_PATH = os.path.expanduser(_sqlite_path)
FALKOR_HOST = os.getenv("FALKOR_HOST", "127.0.0.1")
FALKOR_PORT = int(os.getenv("FALKOR_PORT", "6379"))
GRAPH_NAME = os.getenv("FALKOR_GRAPH", "openclaw_ontology")

# Path to the search_by_date.py script (in auto_memory/ folder)
QDRANT_BY_DATE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "auto_memory", "search_by_date.py")


def _resolve_target_date() -> str:
    """Return target date (YYYY-MM-DD).

    Defaults to local system date. Can be overridden via env REM_SLEEP_DATE.
    """
    env_date = os.environ.get("REM_SLEEP_DATE")
    if env_date:
        # Light validation (full validation happens in search_by_date.py)
        return env_date.strip()
    return date.today().isoformat()


def _fetch_qdrant_entries_for_date(target_date: str) -> dict:
    """Fetch Qdrant entries for target_date via search_by_date.py.

    We intentionally shell out to the script because it is the canonical, recently
    fixed implementation and encapsulates Qdrant payload filtering.

    Returns a dict that is safe to embed into the extract JSON.
    """
    result: dict = {"date": target_date, "ok": False, "raw": "", "error": None}

    if not os.path.exists(QDRANT_BY_DATE_SCRIPT):
        result["error"] = f"Qdrant date search script not found: {QDRANT_BY_DATE_SCRIPT}"
        return result

    try:
        proc = subprocess.run(
            [sys.executable, QDRANT_BY_DATE_SCRIPT, "--date", target_date],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Always keep stdout (even on non-zero exit) for debugging.
        result["raw"] = (proc.stdout or "").strip()
        if proc.returncode == 0:
            result["ok"] = True
        else:
            err = (proc.stderr or "").strip() or f"Non-zero exit code: {proc.returncode}"
            result["error"] = err
    except Exception as e:
        result["error"] = str(e)

    return result


def extract_daily_context():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch all context entries
    cursor.execute("SELECT id, timestamp, scope, content FROM daily_context ORDER BY timestamp ASC")
    rows = cursor.fetchall()

    # Fetch unprocessed learnings
    cursor.execute("SELECT id, timestamp, category, source, content FROM learnings WHERE processed = 0 ORDER BY timestamp ASC")
    lrn_rows = cursor.fetchall()

    conn.close()

    target_date = _resolve_target_date()
    qdrant_dump = _fetch_qdrant_entries_for_date(target_date)

    output = {
        "context": {},
        "learnings": [
            {"id": r[0], "time": r[1], "category": r[2], "source": r[3], "content": r[4]}
            for r in lrn_rows
        ],
        # Additional context layer for REM sleep: raw daily Qdrant dump
        # (vector DB / long-term memory stream)
        "qdrant": qdrant_dump,
    }

    for r in rows:
        scope = r[2]
        if scope not in output["context"]:
            output["context"][scope] = []
        output["context"][scope].append({"id": r[0], "time": r[1], "content": r[3]})

    print(json.dumps(output, indent=2, ensure_ascii=False))

def compress_context(summary_json_str):
    try:
        summaries = json.loads(summary_json_str)
    except Exception as e:
        print(f"Error parsing summaries (JSON expected): {e}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete old context entries
    cursor.execute("DELETE FROM daily_context")
    
    # Insert compressed summaries as one new entry per scope
    # Set timestamp to 23:59 of the current/previous day
    summary_time = datetime.now().replace(hour=23, minute=59, second=59).isoformat()
    
    for scope, text in summaries.items():
        if text.strip():
            cursor.execute(
                "INSERT INTO daily_context (timestamp, scope, content) VALUES (?, ?, ?)",
                (summary_time, scope, f"Summary: {text}")
            )
    
    # Mark learnings as processed
    cursor.execute("UPDATE learnings SET processed = 1 WHERE processed = 0")
    
    conn.commit()
    conn.close()
    print("✅ Short-term memory successfully compressed and cleaned up.")

def ingest_graph(cypher_json_str):
    try:
        queries = json.loads(cypher_json_str)
    except Exception as e:
        print(f"Error parsing Cypher queries (JSON array expected): {e}")
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
                print(f"Error on query '{q}': {e}")
                
    print(f"✅ {success_count}/{len(queries)} Cypher queries successfully ingested into FalkorDB.")

def ingest_learnings(learnings_json_str):
    """Ingest learnings as :Learning nodes into FalkorDB.

    Expected JSON format:
    [
        {"id": 1, "content": "...", "category": "fact", "source": "conversation"},
        ...
    ]

    Each learning becomes a (:Learning) node with properties:
      content, category, source, date
    """
    try:
        learnings = json.loads(learnings_json_str)
    except Exception as e:
        print(f"Error parsing learnings (JSON array expected): {e}")
        sys.exit(1)

    db = FalkorDB(host=FALKOR_HOST, port=FALKOR_PORT)
    graph = db.select_graph(GRAPH_NAME)

    today = _resolve_target_date()
    success_count = 0
    learning_ids = []

    for item in learnings:
        content = item.get("content", "").strip()
        if not content:
            continue

        category = item.get("category", "general")
        source = item.get("source", "")
        learning_id = item.get("id")

        # Escape single quotes for Cypher
        safe_content = content.replace("'", "\\'")
        safe_source = (source or "").replace("'", "\\'")
        safe_category = category.replace("'", "\\'")

        query = (
            f"MERGE (l:Learning {{content: '{safe_content}'}}) "
            f"SET l.category = '{safe_category}', "
            f"l.source = '{safe_source}', "
            f"l.date = '{today}'"
        )

        try:
            graph.query(query)
            success_count += 1
            if learning_id is not None:
                learning_ids.append(learning_id)
        except Exception as e:
            print(f"Error ingesting learning: {e}")

    # Mark ingested learnings as processed in SQLite
    if learning_ids:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(learning_ids))
        cursor.execute(f"UPDATE learnings SET processed = 1 WHERE id IN ({placeholders})", learning_ids)
        conn.commit()
        conn.close()

    print(f"✅ {success_count}/{len(learnings)} learnings ingested as :Learning nodes into FalkorDB.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: rem_sleep_v2.py <extract|compress|ingest|ingest_learnings> [json_data]")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "extract":
        extract_daily_context()
    elif action == "compress":
        if len(sys.argv) < 3:
            print("Error: JSON string expected for 'compress'.")
            sys.exit(1)
        compress_context(sys.argv[2])
    elif action == "ingest":
        if len(sys.argv) < 3:
            print("Error: JSON string expected for 'ingest'.")
            sys.exit(1)
        ingest_graph(sys.argv[2])
    elif action == "ingest_learnings":
        if len(sys.argv) < 3:
            print("Error: JSON string expected for 'ingest_learnings'.")
            sys.exit(1)
        ingest_learnings(sys.argv[2])
    else:
        print(f"Unknown action: {action}")
