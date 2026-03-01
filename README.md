# 🧠 AI Memory – Lokales Gedächtnis für OpenClaw

Automatische Vektorisierung und lokale Suche aller OpenClaw-Chat-Einträge.

## Architektur

```
┌─────────────────────┐    watchdog     ┌──────────────────┐
│  JSONL Sessions     │ ──────────────► │  memory_watcher  │
│  (OpenClaw Agent)   │   Dateiänderung │  (Python)        │
└─────────────────────┘                 └────────┬─────────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    ▼                         ▼
                           ┌────────────────┐      ┌─────────────────┐
                           │  Ollama        │      │  Qdrant         │
                           │  nomic-embed   │      │  Vector DB      │
                           │  :11434        │      │  :6333          │
                           └────────────────┘      └─────────────────┘
```

## Voraussetzungen

- **Fedora Linux** mit **Podman** (`sudo dnf install podman`)
- **Python 3.10+** (`sudo dnf install python3 python3-pip`)
- **curl** (für Health-Checks im Setup-Skript)

## Schnellstart

### 1. Container starten

```bash
bash setup.sh
```

Startet **Qdrant** und **Ollama** als Podman-Container und lädt das Embedding-Modell `nomic-embed-text`.

### 2. Python-Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Watcher starten

```bash
python memory_watcher.py
```

Der Watcher überwacht nun `/home/clawdi/.openclaw/agents/main/sessions/` und vektorisiert automatisch jeden neuen Chat-Eintrag.

## Optionen

| Flag | Beschreibung |
|---|---|
| `--sessions-dir /pfad` | Alternatives Sessions-Verzeichnis |
| `--dry-run` | Nur parsen, kein Embedding/Storage |

## Daten in Qdrant abfragen

```bash
# Anzahl gespeicherter Punkte
curl http://localhost:6333/collections/openclaw_memory/points/count

# Collection-Info
curl http://localhost:6333/collections/openclaw_memory
```

### Semantische Suche (Beispiel mit Python)

```python
from qdrant_client import QdrantClient
import requests

client = QdrantClient(host="localhost", port=6333)

# Suchtext → Embedding
query = "Wie funktioniert die Authentifizierung?"
resp = requests.post(
    "http://localhost:11434/api/embed",
    json={"model": "nomic-embed-text", "input": query},
)
vector = resp.json()["embeddings"][0]

# Suche in Qdrant
results = client.query_points(
    collection_name="openclaw_memory",
    query=vector,
    limit=5,
)

for point in results.points:
    print(f"[{point.payload['sender']}] {point.payload['text'][:100]}")
```

## Container verwalten

```bash
# Status prüfen
podman ps

# Container stoppen
podman stop qdrant ollama

# Container neustarten
podman start qdrant ollama

# Logs ansehen
podman logs -f qdrant
podman logs -f ollama
```

## Datenverzeichnisse

| Pfad | Inhalt |
|---|---|
| `/home/clawdi/.qdrant_storage` | Qdrant-Datenbank (persistiert) |
| `/home/clawdi/.openclaw/agents/main/sessions/` | OpenClaw JSONL-Dateien |
