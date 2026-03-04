#!/usr/bin/env python3
"""
migrate_ontology.py – Migrates data from graph.jsonl into FalkorDB
===================================================================

Reads the existing ontology (JSONL) and transfers it into the
new FalkorDB graph.
"""

import json
import logging
import os
from pathlib import Path
from falkor_client import FalkorMemory

# ── Configuration ──────────────────────────────────────────────────────────

ONTOLOGY_FILE = "/home/clawdi/.openclaw/workspace/memory/ontology/graph.jsonl"

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("migration")

# ── Migration ───────────────────────────────────────────────────────────────

def migrate():
    if not os.path.exists(ONTOLOGY_FILE):
        log.error(f"Ontology file not found: {ONTOLOGY_FILE}")
        return

    client = FalkorMemory()
    log.info("Starting migration from JSONL to FalkorDB...")

    # First import all nodes
    nodes_imported = 0
    relations_imported = 0

    with open(ONTOLOGY_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Pass 1: Nodes
    log.info("Step 1: Creating nodes...")
    for line in lines:
        try:
            data = json.loads(line)
            if data.get("op") == "create":
                entity = data["entity"]
                # Map 'id' to an 'ext_id' property in FalkorDB
                # so we can use it for linking later.
                props = entity.get("properties", {})
                props["ext_id"] = entity["id"]
                
                # Cypher for node creation
                label = entity["type"]
                props_str = ", ".join([f"{k}: {json.dumps(v)}" for k, v in props.items()])
                cypher = f"MERGE (n:{label} {{ext_id: '{entity['id']}'}}) SET n += {{{props_str}}}"
                client.query(cypher)
                nodes_imported += 1
        except Exception as e:
            log.warning(f"Error importing node: {e}")

    log.info(f"{nodes_imported} nodes processed.")

    # Pass 2: Relations
    log.info("Step 2: Linking relationships...")
    for line in lines:
        try:
            data = json.loads(line)
            if data.get("op") == "relate":
                from_id = data["from"]
                to_id = data["to"]
                rel_type = data["rel"]
                
                cypher = f"""
                MATCH (a {{ext_id: '{from_id}'}}), (b {{ext_id: '{to_id}'}})
                MERGE (a)-[r:{rel_type}]->(b)
                RETURN r
                """
                client.query(cypher)
                relations_imported += 1
        except Exception as e:
            log.warning(f"Error linking relationship: {e}")

    log.info(f"{relations_imported} relationships processed.")
    log.info("Migration complete! 🚀")

if __name__ == "__main__":
    migrate()
