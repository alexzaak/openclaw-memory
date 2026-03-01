#!/usr/bin/env bash
# ============================================================================
# setup.sh – Podman Setup für Qdrant, Ollama, FalkorDB & Dashboard
# ============================================================================
# Startet die komplette KI-Infrastruktur.
# Nutzung:  bash setup.sh
# ============================================================================

set -euo pipefail

# ── Farben ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Konfiguration ──────────────────────────────────────────────────────────
QDRANT_CONTAINER="qdrant"
QDRANT_IMAGE="docker.io/qdrant/qdrant:latest"
QDRANT_STORAGE="/home/clawdi/.qdrant_storage"
QDRANT_PORT_HTTP=6333
QDRANT_PORT_GRPC=6334

OLLAMA_CONTAINER="ollama"
OLLAMA_IMAGE="docker.io/ollama/ollama:latest"
OLLAMA_PORT=11434

FALKOR_CONTAINER="falkordb"
FALKOR_IMAGE="docker.io/falkordb/falkordb:latest"
FALKOR_PORT=6379
FALKOR_STORAGE="/home/clawdi/.falkor_storage"

EMBED_MODEL="nomic-embed-text"

FALKOR_CONTAINER="falkordb"
FALKOR_IMAGE="docker.io/falkordb/falkordb:latest"
FALKOR_PORT=6379
FALKOR_STORAGE="/home/clawdi/.falkor_storage"

DASHBOARD_CONTAINER="brain-dashboard"
DASHBOARD_IMAGE="docker.io/library/nginx:alpine"
DASHBOARD_PORT=8000
WORKSPACE_DIR="/home/clawdi/.openclaw/workspace/openclaw-memory"

# ── Hilfsfunktionen ────────────────────────────────────────────────────────

container_running() {
    podman ps --format '{{.Names}}' | grep -qw "$1"
}

container_exists() {
    podman ps -a --format '{{.Names}}' | grep -qw "$1"
}

# ── Qdrant ──────────────────────────────────────────────────────────────────

start_qdrant() {
    info "Prüfe Qdrant-Container …"
    if container_running "$QDRANT_CONTAINER"; then
        info "Qdrant läuft bereits ✓"
    elif container_exists "$QDRANT_CONTAINER"; then
        warn "Qdrant existiert, wird gestartet …"
        podman start "$QDRANT_CONTAINER"
    else
        mkdir -p "$QDRANT_STORAGE"
        info "Starte Qdrant …"
        podman run -d --name "$QDRANT_CONTAINER" --restart always -p "${QDRANT_PORT_HTTP}:6333" -p "${QDRANT_PORT_GRPC}:6334" -v "${QDRANT_STORAGE}:/qdrant/storage:Z" "$QDRANT_IMAGE"
    fi

    info "Warte auf Qdrant (Port $QDRANT_PORT_HTTP) …"
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${QDRANT_PORT_HTTP}/healthz" > /dev/null 2>&1; then
            info "Qdrant ist bereit ✓"
            return
        fi
        sleep 1
    done
    error "Qdrant ist nach 30 Sekunden nicht erreichbar!"
    exit 1
}

# ── Ollama ──────────────────────────────────────────────────────────────────

start_ollama() {
    info "Prüfe Ollama-Container …"
    if container_running "$OLLAMA_CONTAINER"; then
        info "Ollama läuft bereits ✓"
    elif container_exists "$OLLAMA_CONTAINER"; then
        warn "Ollama existiert, wird gestartet …"
        podman start "$OLLAMA_CONTAINER"
    else
        info "Starte Ollama …"
        podman run -d --name "$OLLAMA_CONTAINER" --restart always -p "${OLLAMA_PORT}:11434" -v ollama_data:/root/.ollama:Z "$OLLAMA_IMAGE"
    fi
    info "Lade Modell ${EMBED_MODEL} …"
    podman exec "$OLLAMA_CONTAINER" ollama pull "$EMBED_MODEL" || true
}

    info "Warte auf Ollama (Port $OLLAMA_PORT) …"
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${OLLAMA_PORT}/" > /dev/null 2>&1; then
            info "Ollama ist bereit ✓"
            break
        fi
        sleep 1
    done

start_falkordb() {
    info "Prüfe FalkorDB-Container …"
    if container_running "$FALKOR_CONTAINER"; then
        info "FalkorDB läuft bereits ✓"
    elif container_exists "$FALKOR_CONTAINER"; then
        warn "FalkorDB existiert, wird gestartet …"
        podman start "$FALKOR_CONTAINER"
    else
        mkdir -p "$FALKOR_STORAGE"
        info "Starte FalkorDB …"
        podman run -d --name "$FALKOR_CONTAINER" --restart always -p "${FALKOR_PORT}:6379" -v "${FALKOR_STORAGE}:/data:Z" "$FALKOR_IMAGE"
    fi
}


# ── FalkorDB ────────────────────────────────────────────────────────────────

start_falkordb() {
    info "Prüfe FalkorDB-Container …"

    if container_running "$FALKOR_CONTAINER"; then
        info "FalkorDB läuft bereits ✓"
        return
    fi

    if container_exists "$FALKOR_CONTAINER"; then
        warn "FalkorDB-Container existiert, wird neu gestartet …"
        podman start "$FALKOR_CONTAINER"
    else
        info "Erstelle FalkorDB-Storage-Verzeichnis: $FALKOR_STORAGE"
        mkdir -p "$FALKOR_STORAGE"

        info "Starte FalkorDB-Container …"
        podman run -d \
            --name "$FALKOR_CONTAINER" \
            --restart always \
            -p "${FALKOR_PORT}:6379" \
            -v "${FALKOR_STORAGE}:/data:Z" \
            "$FALKOR_IMAGE"
    fi

    info "Warte auf FalkorDB (Port $FALKOR_PORT) …"
    # Simple netcat check if redis-cli is not available
    for i in $(seq 1 10); do
        if nc -z 127.0.0.1 $FALKOR_PORT > /dev/null 2>&1 || (echo > /dev/tcp/127.0.0.1/$FALKOR_PORT) > /dev/null 2>&1; then
            info "FalkorDB ist bereit ✓"
            return
        fi
        sleep 1
    done
    error "FalkorDB ist nach 10 Sekunden nicht erreichbar!"
    exit 1
}

# ── Main ────────────────────────────────────────────────────────────────────

main() {
    echo "=============================================="
    echo "  AI Memory – Podman Infrastructure Setup"
    echo "=============================================="
    echo ""

start_dashboard() {
    info "Prüfe Dashboard-Container …"
    if container_running "$DASHBOARD_CONTAINER"; then
        info "Dashboard läuft bereits ✓"
    else
        if container_exists "$DASHBOARD_CONTAINER"; then
            podman rm -f "$DASHBOARD_CONTAINER"
        fi
        info "Starte Dashboard auf Port $DASHBOARD_PORT …"
        podman run -d --name "$DASHBOARD_CONTAINER" --restart always -p "${DASHBOARD_PORT}:80" -v "${WORKSPACE_DIR}:/usr/share/nginx/html:ro,Z" "$DASHBOARD_IMAGE"
    fi
}

# ── Main ────────────────────────────────────────────────────────────────────

main() {
    start_qdrant
    start_ollama
    echo ""
    start_falkordb
    start_dashboard

    echo ""
    echo "=============================================="
    info "Setup abgeschlossen! 🚀"
    echo ""
    info "Qdrant:  http://127.0.0.1:${QDRANT_PORT_HTTP}"
    info "Ollama:  http://127.0.0.1:${OLLAMA_PORT}"
    info "FalkorDB: redis://127.0.0.1:${FALKOR_PORT}"
    echo ""
    info "Nächster Schritt:"
    info "  pip install -r requirements.txt"
    info "  python memory_watcher.py"
    echo "=============================================="
}

main "$@"
