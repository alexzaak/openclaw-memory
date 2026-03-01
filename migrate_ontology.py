#!/usr/bin/env python3
"""
migrate_ontology.py – Migriert Daten von graph.jsonl in FalkorDB
================================================================

Liest die bestehende Ontologie (JSONL) und überführt sie in den 
neuen FalkorDB-Graphen.
"""

import json
import logging
import os
from pathlib import Path
from falkor_client import FalkorMemory

# ── Konfiguration ──────────────────────────────────────────────────────────

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
        log.error(f"Ontologie-Datei nicht gefunden: {ONTOLOGY_FILE}")
        return

    client = FalkorMemory()
    log.info("Starte Migration von JSONL zu FalkorDB...")

    # Zuerst alle Knoten importieren
    nodes_imported = 0
    relations_imported = 0

    with open(ONTOLOGY_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Pass 1: Nodes
    log.info("Schritt 1: Knoten erstellen...")
    for line in lines:
        try:
            data = json.loads(line)
            if data.get("op") == "create":
                entity = data["entity"]
                # Wir mappen 'id' auf eine Eigenschaft 'ext_id' in FalkorDB
                # um sie später für Verknüpfungen nutzen zu können.
                props = entity.get("properties", {})
                props["ext_id"] = entity["id"]
                
                # Cypher für Node creation
                label = entity["type"]
                props_str = ", ".join([f"{k}: {json.dumps(v)}" for k, v in props.items()])
                cypher = f"MERGE (n:{label} {{ext_id: '{entity['id']}'}}) SET n += {{{props_str}}}"
                client.query(cypher)
                nodes_imported += 1
        except Exception as e:
            log.warning(f"Fehler beim Importieren eines Knotens: {e}")

    log.info(f"{nodes_imported} Knoten verarbeitet.")

    # Pass 2: Relations
    log.info("Schritt 2: Beziehungen verknüpfen...")
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
            log.warning(f"Fehler beim Verknüpfen einer Beziehung: {e}")

    log.info(f"{relations_imported} Beziehungen verarbeitet.")
    log.info("Migration abgeschlossen! 🚀")

if __name__ == "__main__":
    migrate()
