#!/usr/bin/env bash
# ============================================================================
# setup.sh – Podman Setup für Qdrant & Ollama
# ============================================================================
# Startet die Container für die lokale AI-Memory-Infrastruktur.
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

EMBED_MODEL="nomic-embed-text"

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
        return
    fi

    if container_exists "$QDRANT_CONTAINER"; then
        warn "Qdrant-Container existiert, wird neu gestartet …"
        podman start "$QDRANT_CONTAINER"
    else
        info "Erstelle Qdrant-Storage-Verzeichnis: $QDRANT_STORAGE"
        mkdir -p "$QDRANT_STORAGE"

        info "Starte Qdrant-Container …"
        podman run -d \
            --name "$QDRANT_CONTAINER" \
            --restart always \
            -p "${QDRANT_PORT_HTTP}:6333" \
            -p "${QDRANT_PORT_GRPC}:6334" \
            -v "${QDRANT_STORAGE}:/qdrant/storage:Z" \
            "$QDRANT_IMAGE"
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
        warn "Ollama-Container existiert, wird neu gestartet …"
        podman start "$OLLAMA_CONTAINER"
    else
        info "Starte Ollama-Container …"
        podman run -d \
            --name "$OLLAMA_CONTAINER" \
            --restart always \
            -p "${OLLAMA_PORT}:11434" \
            -v ollama_data:/root/.ollama:Z \
            "$OLLAMA_IMAGE"
    fi

    info "Warte auf Ollama (Port $OLLAMA_PORT) …"
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${OLLAMA_PORT}/" > /dev/null 2>&1; then
            info "Ollama ist bereit ✓"
            break
        fi
        sleep 1
    done

    info "Lade Embedding-Modell: ${EMBED_MODEL} …"
    podman exec "$OLLAMA_CONTAINER" ollama pull "$EMBED_MODEL"
    info "Modell ${EMBED_MODEL} geladen ✓"
}

# ── Main ────────────────────────────────────────────────────────────────────

main() {
    echo "=============================================="
    echo "  AI Memory – Podman Infrastructure Setup"
    echo "=============================================="
    echo ""

    # Podman prüfen
    if ! command -v podman &> /dev/null; then
        error "Podman ist nicht installiert! Bitte zuerst installieren:"
        error "  sudo dnf install podman"
        exit 1
    fi

    start_qdrant
    echo ""
    start_ollama

    echo ""
    echo "=============================================="
    info "Setup abgeschlossen! 🚀"
    echo ""
    info "Qdrant:  http://127.0.0.1:${QDRANT_PORT_HTTP}"
    info "Ollama:  http://127.0.0.1:${OLLAMA_PORT}"
    echo ""
    info "Nächster Schritt:"
    info "  pip install -r requirements.txt"
    info "  python memory_watcher.py"
    echo "=============================================="
}

main "$@"
