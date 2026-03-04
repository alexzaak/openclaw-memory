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
- `graph_rem_sleep.py`: The "REM processor" for nightly fact extraction.
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
A cron job (recommended at 23:30) should run the following command:
```bash
# Extracts today's learned facts and updates the graph + dashboard
python3 graph_rem_sleep.py process_today
```

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
