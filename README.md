# 🧠 AI Memory – Lokales Gedächtnis für OpenClaw

Vollautomatisches, semantisches und strukturiertes Langzeitgedächtnis für Clawdi (OpenClaw).

## Architektur

Das System besteht aus drei Kern-Komponenten, die Hand in Hand arbeiten:

1.  **Auto-Memory (Vektor-Suche):** Jede Chat-Nachricht wird in Echtzeit vektorisiert und in Qdrant gespeichert. Erlaubt semantische Suche ("Gefühlssuche").
2.  **Wissensgraph (Struktur):** Fakten und Beziehungen (Personen, Projekte, Hardware) werden in FalkorDB (Graph-DB) gespeichert.
3.  **REM-Schlaf (Synthese):** Ein nächtlicher Cron-Job analysiert die Tages-Chats und überführt neue Erkenntnisse automatisch in den Wissensgraphen.

```
┌─────────────────────┐    watchdog     ┌──────────────────┐
│  JSONL Sessions     │ ──────────────► │  memory_watcher  │
│  (OpenClaw Agent)   │   Dateiänderung │  (Python Service)│
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

## Komponenten & Tools

### 🏗️ Infrastruktur (Podman)
- **Qdrant:** Vektor-Datenbank für semantische Suche.
- **Ollama:** Lokale Embedding-Engine (`nomic-embed-text`).
- **FalkorDB:** Hochperformante Graph-Datenbank für Ontologien.
- **Nginx:** Webserver für die Visualisierung.

### 🐍 Python Core
- `memory_watcher.py`: Überwacht die Session-Files und füttert Qdrant.
- `falkor_client.py`: Interface für Cypher-Abfragen an die Graph-DB.
- `graph_rem_sleep.py`: Der "REM-Prozessor" für die nächtliche Fakten-Extraktion.
- `generate_brain_map.py`: Generiert die interaktive HTML-Visualisierung.

## Schnellstart

### 1. Vorbereiten (Fedora LVM-Fix)
Fedora weist der Root-Partition oft nur 15GB zu. Für die Container-Images sollte der Speicher erweitert werden:
```bash
sudo lvextend -l +100%FREE /dev/mapper/fedora_nova-root
sudo xfs_growfs /
```

### 2. Infrastruktur starten
```bash
bash setup.sh
```
Dies startet alle Container und lädt die benötigten KI-Modelle.

### 3. Dependencies & Service
```bash
pip install -r requirements.txt
# Watcher als User-Service starten
systemctl --user enable --now clawdi-memory.service
```

## Wartung & Betrieb

### Nächtliche Analyse (REM-Schlaf)
Ein Cron-Job (empfohlen 23:30 Uhr) sollte folgendes Kommando ausführen:
```bash
# Extrahiert heute gelernte Fakten und aktualisiert den Graphen + Dashboard
python3 graph_rem_sleep.py process_today
```

### Migration alter Daten
Um bestehende JSONL-Logs oder Markdown-Dateien zu importieren:
```bash
python3 import_history.py    # Importiert alle Sessions in Qdrant
python3 migrate_ontology.py  # Importiert bestehende graph.jsonl in FalkorDB
```

## Visualisierung
Das interaktive Dashboard ist im lokalen Netzwerk erreichbar:
`http://<server-ip>:8000`

- **Rot:** Personen
- **Gelb:** Projekte
- **Blau:** Sonstige Entitäten (Events, Tasks, Locations)

## Ports

| Service | Port | Externer Zugriff |
|---|---|---|
| Dashboard | 8000 | Ja (Firewall öffnen!) |
| Qdrant | 6333 | Nein (Localhost) |
| Ollama | 11434 | Nein (Localhost) |
| FalkorDB | 6379 | Nein (Localhost) |
