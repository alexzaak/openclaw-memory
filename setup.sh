#!/usr/bin/env bash
# ============================================================================
# setup.sh – Podman Setup for Qdrant, Ollama, FalkorDB & Dashboard
# ============================================================================
# Starts the complete AI infrastructure.
# Configuration is loaded from .env (if present).
# Usage:  bash setup.sh
# ============================================================================

set -euo pipefail

# ── Load .env ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Configuration (overridable via .env) ───────────────────────────────────
QDRANT_CONTAINER="qdrant"
QDRANT_IMAGE="docker.io/qdrant/qdrant:latest"
QDRANT_STORAGE="${QDRANT_STORAGE:-/home/clawdi/.qdrant_storage}"
QDRANT_PORT_HTTP="${QDRANT_PORT:-6333}"
QDRANT_PORT_GRPC=6334

OLLAMA_CONTAINER="ollama"
OLLAMA_IMAGE="docker.io/ollama/ollama:latest"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"

FALKOR_CONTAINER="falkordb"
FALKOR_IMAGE="docker.io/falkordb/falkordb:latest"
FALKOR_PORT="${FALKOR_PORT:-6379}"
FALKOR_STORAGE="${FALKOR_STORAGE:-/home/clawdi/.falkor_storage}"

EMBED_MODEL="${EMBED_MODEL:-nomic-embed-text}"

DASHBOARD_CONTAINER="brain-dashboard"
DASHBOARD_IMAGE="docker.io/library/nginx:alpine"
DASHBOARD_PORT="${DASHBOARD_PORT:-8000}"
WORKSPACE_DIR="/home/clawdi/.openclaw/workspace/openclaw-memory"

# ── Helper Functions ────────────────────────────────────────────────────────

container_running() {
    podman ps --format '{{.Names}}' | grep -qw "$1"
}

container_exists() {
    podman ps -a --format '{{.Names}}' | grep -qw "$1"
}

# ── Qdrant ──────────────────────────────────────────────────────────────────

start_qdrant() {
    info "Checking Qdrant container …"
    if container_running "$QDRANT_CONTAINER"; then
        info "Qdrant is already running ✓"
    elif container_exists "$QDRANT_CONTAINER"; then
        warn "Qdrant exists, starting …"
        podman start "$QDRANT_CONTAINER"
    else
        mkdir -p "$QDRANT_STORAGE"
        info "Starting Qdrant …"
        podman run -d --name "$QDRANT_CONTAINER" --restart always -p "${QDRANT_PORT_HTTP}:6333" -p "${QDRANT_PORT_GRPC}:6334" -v "${QDRANT_STORAGE}:/qdrant/storage:Z" "$QDRANT_IMAGE"
    fi

    info "Waiting for Qdrant (port $QDRANT_PORT_HTTP) …"
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${QDRANT_PORT_HTTP}/healthz" > /dev/null 2>&1; then
            info "Qdrant is ready ✓"
            return
        fi
        sleep 1
    done
    error "Qdrant not reachable after 30 seconds!"
    exit 1
}

# ── Ollama ──────────────────────────────────────────────────────────────────

start_ollama() {
    info "Checking Ollama container …"
    if container_running "$OLLAMA_CONTAINER"; then
        info "Ollama is already running ✓"
    elif container_exists "$OLLAMA_CONTAINER"; then
        warn "Ollama exists, starting …"
        podman start "$OLLAMA_CONTAINER"
    else
        info "Starting Ollama …"
        podman run -d --name "$OLLAMA_CONTAINER" --restart always -p "${OLLAMA_PORT}:11434" -v ollama_data:/root/.ollama:Z "$OLLAMA_IMAGE"
    fi

    info "Waiting for Ollama (port $OLLAMA_PORT) …"
    for i in $(seq 1 30); do
        if curl -sf "http://127.0.0.1:${OLLAMA_PORT}/" > /dev/null 2>&1; then
            info "Ollama is ready ✓"
            break
        fi
        sleep 1
    done

    info "Pulling model ${EMBED_MODEL} …"
    podman exec "$OLLAMA_CONTAINER" ollama pull "$EMBED_MODEL" || true
}


start_falkordb() {
    info "Checking FalkorDB container …"

    if container_running "$FALKOR_CONTAINER"; then
        info "FalkorDB is already running ✓"
        return
    fi

    if container_exists "$FALKOR_CONTAINER"; then
        warn "FalkorDB container exists, restarting …"
        podman start "$FALKOR_CONTAINER"
    else
        info "Creating FalkorDB storage directory: $FALKOR_STORAGE"
        mkdir -p "$FALKOR_STORAGE"

        info "Starting FalkorDB container …"
        podman run -d \
            --name "$FALKOR_CONTAINER" \
            --restart always \
            -p "${FALKOR_PORT}:6379" \
            -v "${FALKOR_STORAGE}:/data:Z" \
            "$FALKOR_IMAGE"
    fi

    info "Waiting for FalkorDB (port $FALKOR_PORT) …"
    # Simple netcat check if redis-cli is not available
    for i in $(seq 1 10); do
        if nc -z 127.0.0.1 $FALKOR_PORT > /dev/null 2>&1 || (echo > /dev/tcp/127.0.0.1/$FALKOR_PORT) > /dev/null 2>&1; then
            info "FalkorDB is ready ✓"
            return
        fi
        sleep 1
    done
    error "FalkorDB not reachable after 10 seconds!"
    exit 1
}

# ── Dashboard ──────────────────────────────────────────────────────────────

start_dashboard() {
    info "Checking Dashboard container …"
    if container_running "$DASHBOARD_CONTAINER"; then
        info "Dashboard is already running ✓"
    else
        if container_exists "$DASHBOARD_CONTAINER"; then
            podman rm -f "$DASHBOARD_CONTAINER"
        fi
        info "Starting Dashboard on port $DASHBOARD_PORT …"
        podman run -d --name "$DASHBOARD_CONTAINER" --restart always -p "${DASHBOARD_PORT}:80" -v "${WORKSPACE_DIR}:/usr/share/nginx/html:ro,Z" "$DASHBOARD_IMAGE"
    fi
}

# ── Main ────────────────────────────────────────────────────────────────────

main() {
    echo "=============================================="
    echo "  AI Memory – Podman Infrastructure Setup"
    echo "=============================================="
    echo ""

    start_qdrant
    start_ollama
    echo ""
    start_falkordb
    start_dashboard

    echo ""
    echo "=============================================="
    info "Setup complete! 🚀"
    echo ""
    info "Qdrant:  http://127.0.0.1:${QDRANT_PORT_HTTP}"
    info "Ollama:  http://127.0.0.1:${OLLAMA_PORT}"
    info "FalkorDB: redis://127.0.0.1:${FALKOR_PORT}"
    echo ""
    info "Next step:"
    info "  pip install -r requirements.txt"
    info "  python memory_watcher.py"
    echo "=============================================="
}

main "$@"

