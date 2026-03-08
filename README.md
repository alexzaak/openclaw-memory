# 🧠 AI Memory – Local Memory for OpenClaw

Fully automated, semantic and structured long-term memory for Clawdi (OpenClaw).

## Architecture

The system consists of three core components that work hand in hand:

1.  **Auto-Memory (Vector Search):** Every chat message is vectorized in real-time and stored in Qdrant. Enables semantic search ("feeling-based search").
2.  **Knowledge Graph (Structure):** Facts and relationships (people, projects, hardware) are stored in FalkorDB (graph DB).
3.  **REM Sleep (Synthesis):** A nightly cron job analyzes the day's chats and automatically transfers new insights into the knowledge graph.

```
┌─────────────────────┐    watchdog     ┌──────────────────┐
│  JSONL Sessions     │ ──────────────► │  memory_watcher  │
│  (OpenClaw Agent)   │   file change   │  (Python Service)│
└─────────────────────┘                 └────────┬─────────┘
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            ▼                                    ▼                                    ▼
   ┌────────────────┐                  ┌─────────────────┐                  ┌──────────────────┐
   │  Ollama        │                  │  Qdrant         │                  │  FalkorDB        │
   │  nomic-embed   │                  │  Vector DB      │                  │  Graph DB        │
   │  :11434        │                  │  :6333          │                  │  :6379           │
   └────────────────┘                  └─────────────────┘                  └──────────────────┘
            │                                                                         │
            └────────────────────────────────────┬────────────────────────────────────┘
                                                 ▼
                                       ┌──────────────────┐
                                       │  Brain Dashboard │
                                       │  (Nginx / Port 8000)
                                       └──────────────────┘
```

## Components & Tools

### 🏗️ Infrastructure (Podman)
- **Qdrant:** Vector database for semantic search.
- **Ollama:** Local embedding engine (`nomic-embed-text`).
- **FalkorDB:** High-performance graph database for ontologies.
- **Nginx:** Web server for visualization.

### 🐍 Python Core
- `memory_watcher.py`: Watches session files and feeds Qdrant.
- `falkor_client.py`: Interface for Cypher queries to the graph DB.
- `search_by_date.py`: Canonical utility to dump Qdrant entries for a given date.
- `rem_sleep_v2.py`: REM-sleep helper for extracting daily context (SQLite + Qdrant), compressing SQLite context, and ingesting Cypher into FalkorDB.
- `graph_rem_sleep.py`: Legacy helper (Qdrant extract + Cypher ingest).
- `generate_brain_map.py`: Generates the interactive HTML visualization.

## Quick Start

### 1. Preparation (Fedora LVM Fix)
Fedora often allocates only 15GB to the root partition. Storage should be expanded for the container images:
```bash
sudo lvextend -l +100%FREE /dev/mapper/fedora_nova-root
sudo xfs_growfs /
```

### 2. Start Infrastructure
```bash
bash setup.sh
```
This starts all containers and downloads the required AI models.

### 3. Dependencies & Service
```bash
pip install -r requirements.txt
# Start watcher as user service
systemctl --user enable --now clawdi-memory.service
```

## Maintenance & Operations

### Nightly Analysis (REM Sleep)
The REM-sleep pipeline is split into two steps:

1) **Extract** the day's context as JSON (short-term SQLite + Qdrant daily stream)
2) Let the agent/LLM create summaries + Cypher, then **compress** SQLite and **ingest** into FalkorDB.

#### 1) Extract daily context (SQLite + Qdrant)
```bash
python3 rem_sleep_v2.py extract > /tmp/rem_sleep_context.json
```

By default the target date is the local system date. You can override it:
```bash
REM_SLEEP_DATE=2026-03-08 python3 rem_sleep_v2.py extract
```

`rem_sleep_v2.py` shells out to the canonical Qdrant-by-date script and embeds its output into the JSON under `qdrant`:
```bash
python3 search_by_date.py --date 2026-03-08
```

#### 2) Apply compression + graph ingestion (agent-driven)
After the agent produces (a) scope summaries and (b) Cypher queries:
```bash
python3 rem_sleep_v2.py compress '<json summaries>'
python3 rem_sleep_v2.py ingest   '<json cypher queries>'
```

> Note: `graph_rem_sleep.py` currently only supports `extract` (Qdrant → stdout) and `ingest` (stdin JSON Cypher).

### Migrating Existing Data
To import existing JSONL logs or Markdown files:
```bash
python3 import_history.py    # Imports all sessions into Qdrant
python3 migrate_ontology.py  # Imports existing graph.jsonl into FalkorDB
```

## 🧠 Brain Dashboard

The **Clawdi Brain Dashboard** is a full-stack web application:

- **Neural Feed** – Semantic search through all memories (Qdrant)
- **Knowledge Vault** – Entity explorer for the knowledge graph (FalkorDB)
- **Health Monitor** – System status, temperature history, learning log (SQLite)

### Starting

```bash
# Seed SQLite with demo data
python3 dashboard/seed_sqlite.py

# Start dashboard (backend + frontend)
cd dashboard && podman compose up -d --build
```

Dashboard available at: `http://<server-ip>:80`
API Docs: `http://<server-ip>:8080/docs`

### Development (Local)

```bash
# Backend
cd dashboard/backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8080

# Frontend (in a separate terminal)
cd dashboard/frontend && npm install && npm run dev
```

## Ports

| Service | Port | Description |
|---|---|---|
| Dashboard UI | 80 | Nginx + React SPA |
| Dashboard API | 8080 | FastAPI Backend |
| Qdrant | 6333 | Vector Database |
| Ollama | 11434 | Embedding Engine |
| FalkorDB | 6379 | Graph Database |
