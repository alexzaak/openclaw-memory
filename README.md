# 🧠 AI Memory – Local Memory for OpenClaw

Fully automated, semantic and structured long-term memory for Clawdi (OpenClaw).

## Architecture

The system consists of four core components that work hand in hand:

1.  **Auto-Memory (Vector Search):** Every chat message is vectorized in real-time and stored in Qdrant. Enables semantic search ("feeling-based search").
2.  **Knowledge Graph (Structure):** Facts and relationships (people, projects, hardware) are stored in FalkorDB (graph DB).
3.  **Short-Term Memory (Context):** Day-to-day context — current moods, plans, reminders — is stored in a local SQLite database. Scoped per person (alex, laura, family, system) and compressed nightly by REM Sleep.
4.  **REM Sleep (Synthesis):** A nightly pipeline reads the day's chats + short-term context, compresses SQLite entries into summaries, and transfers new insights into the knowledge graph.

```
┌─────────────────────┐    watchdog     ┌──────────────────┐
│  JSONL Sessions     │ ──────────────► │  memory_watcher  │
│  (OpenClaw Agent)   │   file change   │  (Python Service)│
└─────────────────────┘                 └────────┬─────────┘
                                                 │
      ┌──────────────────────┬───────────────────┼───────────────────┐
      ▼                      ▼                   ▼                   ▼
┌────────────┐     ┌─────────────────┐  ┌──────────────────┐ ┌──────────────┐
│  Ollama    │     │  Qdrant         │  │  FalkorDB        │ │  SQLite      │
│  nomic-    │     │  Vector DB      │  │  Graph DB        │ │  Short-Term  │
│  embed     │     │  :6333          │  │  :6379           │ │  Memory      │
│  :11434    │     │  (Long-Term)    │  │  (Knowledge)     │ │  (Context)   │
└────────────┘     └─────────────────┘  └──────────────────┘ └──────┬───────┘
      │                     │                    │                  │
      │                     │                    │    add_context ▲ │ ▼ get_context
      │                     │                    │           ┌──────┴───────┐
      │                     │                    │           │  Agent CLI   │
      │                     │                    │           └──────────────┘
      └─────────────────────┴────────────────────┴──────────────────┐
                                                                   ▼
                                                         ┌──────────────────┐
                                                         │  Brain Dashboard │
                                                         │  (Nginx / :8000) │
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
- `search.py` / `search_by_date.py`: CLI utilities for querying Qdrant (semantic search / date filter).
- `add_context.py`: Adds an entry to short-term memory (SQLite).
- `get_context.py`: Retrieves recent short-term memory entries by scope.
- `migrate_short_term.py`: Creates the `daily_context` SQLite table (initial setup).
- `rem_sleep_v2.py`: REM-sleep pipeline — extract daily context (SQLite + Qdrant), compress SQLite entries, ingest Cypher into FalkorDB.
- `graph_rem_sleep.py`: Legacy helper (Qdrant extract + Cypher ingest).
- `generate_brain_map.py`: Generates the interactive HTML visualization.

## Quick Start

### 1. Configuration

All scripts read their configuration from a single `.env` file in the project root. A template is provided:

```bash
cp .env.example .env
# Edit .env to match your environment
```

| Variable | Default | Used By |
|---|---|---|
| `QDRANT_HOST` | `127.0.0.1` | all Python scripts, setup.sh |
| `QDRANT_PORT` | `6333` | all Python scripts, setup.sh |
| `QDRANT_COLLECTION` | `openclaw_memory` | memory_watcher, backend |
| `QDRANT_STORAGE` | `/home/clawdi/.qdrant_storage` | setup.sh |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | memory_watcher, graph_rem_sleep |
| `EMBED_MODEL` | `nomic-embed-text` | memory_watcher, setup.sh |
| `EMBED_DIMENSION` | `768` | memory_watcher, backend |
| `FALKOR_HOST` | `127.0.0.1` | falkor_client, backend |
| `FALKOR_PORT` | `6379` | falkor_client, setup.sh |
| `FALKOR_GRAPH` | `openclaw_ontology` | falkor_client, backend |
| `FALKOR_STORAGE` | `/home/clawdi/.falkor_storage` | setup.sh |
| `SESSIONS_DIR` | `/home/clawdi/.openclaw/agents/main/sessions/` | memory_watcher |
| `SQLITE_PATH` | `~/.openclaw/short_term.db` | seed_sqlite, backend |
| `ONTOLOGY_FILE` | (see .env.example) | migrate_ontology |
| `DASHBOARD_PORT` | `8000` | setup.sh |
| `API_PORT` | `8080` | backend |
| `CORS_ORIGINS` | `*` | backend |

> **Note:** The `.env` file is excluded from git via `.gitignore`. Never commit secrets to version control.

### 2. Preparation (Fedora LVM Fix)
Fedora often allocates only 15GB to the root partition. Storage should be expanded for the container images:
```bash
sudo lvextend -l +100%FREE /dev/mapper/fedora_nova-root
sudo xfs_growfs /
```

### 3. Start Infrastructure
```bash
bash setup.sh
```
This starts all containers and downloads the required AI models.

### 4. Dependencies & Service
```bash
pip install -r requirements.txt
# Start watcher as user service
systemctl --user enable --now clawdi-memory.service
```

## Maintenance & Operations

### Short-Term Memory (SQLite)

The short-term memory stores day-to-day context — moods, plans, reminders — in a local SQLite database (`SQLITE_PATH`, default `~/.openclaw/short_term.db`). Entries are scoped per person or domain.

**Initial setup** (creates the `daily_context` table):
```bash
python3 migrate_short_term.py
```

**Adding context** (called by the agent during conversations):
```bash
python3 add_context.py --scope alex  --text "Currently refactoring the memory system"
python3 add_context.py --scope laura --text "Has an exam on Thursday"
python3 add_context.py --scope system --text "Qdrant restarted after OOM"
```

**Reading context** (used by the agent at the start of each session):
```bash
python3 get_context.py --scope alex           # Last 48h for alex + family + system
python3 get_context.py --scope laura --hours 24  # Last 24h
```

| Scope | Purpose |
|---|---|
| `alex` | Personal context for Alex |
| `laura` | Personal context for Laura |
| `family` | Shared family context |
| `system` | Infrastructure notes, errors, maintenance |

> **Lifecycle:** Entries accumulate during the day. The nightly **REM Sleep** pipeline compresses them into summaries and clears the table — keeping short-term memory lean.

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

### Backup & Restore

All three databases can be backed up and restored with a single command. Backups are stored in `BACKUP_DIR` (default `~/.openclaw/backups`), organized by database type.

**Backup:**
```bash
bash backup.sh              # Backup all databases
bash backup.sh qdrant       # Backup Qdrant only
bash backup.sh falkordb     # Backup FalkorDB only
bash backup.sh sqlite       # Backup SQLite only
```

**Restore:**
```bash
# Restore from a specific backup file
bash restore.sh qdrant    ~/.openclaw/backups/qdrant/qdrant_openclaw_memory_20260310.snapshot
bash restore.sh falkordb  ~/.openclaw/backups/falkordb/falkordb_20260310.rdb
bash restore.sh sqlite    ~/.openclaw/backups/sqlite/short_term_20260310.db

# Restore from the latest available backup
bash restore.sh --latest all        # Restore all databases
bash restore.sh --latest sqlite     # Restore SQLite only
```

| Method | Qdrant | FalkorDB | SQLite |
|---|---|---|---|
| **Backup** | REST snapshot API | `redis-cli BGSAVE` + copy | `sqlite3 .backup` |
| **Restore** | Snapshot recover API | Stop → replace RDB → restart | File copy |
| **Output** | `.snapshot` | `.rdb` | `.db` |

**Scheduling (cron):**
```cron
# Daily backup at 02:00
0 2 * * * cd /path/to/openclaw-memory && bash backup.sh >> /var/log/clawdi-backup.log 2>&1
```

| Variable | Default | Description |
|---|---|---|
| `BACKUP_DIR` | `~/.openclaw/backups` | Directory for backup files |
| `BACKUP_RETAIN` | `5` | Number of backups to keep per database |

> **Safety:** `restore.sh` always creates a pre-restore backup before overwriting data and asks for confirmation.

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
