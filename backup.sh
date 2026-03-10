#!/usr/bin/env bash
# ============================================================================
# backup.sh – Backup Qdrant, FalkorDB & SQLite
# ============================================================================
# Usage:
#   bash backup.sh              # Backup all databases
#   bash backup.sh qdrant       # Backup Qdrant only
#   bash backup.sh falkordb     # Backup FalkorDB only
#   bash backup.sh sqlite       # Backup SQLite only
#
# Configuration is loaded from .env (BACKUP_DIR, BACKUP_RETAIN, etc.)
# ============================================================================

set -euo pipefail

# ── Load .env ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a
    source "${SCRIPT_DIR}/.env"
    set +a
fi

# ── Configuration ───────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-$HOME/.openclaw/backups}"
BACKUP_DIR="${BACKUP_DIR/#\~/$HOME}"
BACKUP_RETAIN="${BACKUP_RETAIN:-5}"

QDRANT_HOST="${QDRANT_HOST:-127.0.0.1}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
QDRANT_COLLECTION="${QDRANT_COLLECTION:-openclaw_memory}"

FALKOR_PORT="${FALKOR_PORT:-6379}"
FALKOR_CONTAINER="${FALKOR_CONTAINER:-falkordb}"

SQLITE_PATH="${SQLITE_PATH:-$HOME/.openclaw/short_term.db}"
SQLITE_PATH="${SQLITE_PATH/#\~/$HOME}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[BACKUP]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}    $*"; }
error() { echo -e "${RED}[ERROR]${NC}   $*"; }
header(){ echo -e "${CYAN}$*${NC}"; }

# ── Helper: rotate old backups ──────────────────────────────────────────────
rotate_backups() {
    local prefix="$1"
    local dir="$2"
    local keep="${BACKUP_RETAIN}"

    local count
    count=$(find "$dir" -maxdepth 1 -name "${prefix}*" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$count" -gt "$keep" ]]; then
        local to_delete=$((count - keep))
        info "Rotating: removing ${to_delete} old ${prefix} backup(s)"
        find "$dir" -maxdepth 1 -name "${prefix}*" -type f -print0 \
            | sort -z \
            | head -z -n "$to_delete" \
            | xargs -0 rm -f
    fi
}

# ── Qdrant Backup ───────────────────────────────────────────────────────────
backup_qdrant() {
    local dest_dir="${BACKUP_DIR}/qdrant"
    mkdir -p "$dest_dir"

    info "Creating Qdrant snapshot for collection '${QDRANT_COLLECTION}' ..."

    # 1. Trigger snapshot creation
    local response
    response=$(curl -sf -X POST \
        "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots" \
        -H "Content-Type: application/json" 2>&1) || {
        error "Failed to create Qdrant snapshot. Is Qdrant running on ${QDRANT_HOST}:${QDRANT_PORT}?"
        return 1
    }

    # 2. Extract snapshot name from response
    local snapshot_name
    snapshot_name=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['name'])" 2>/dev/null) || {
        error "Failed to parse snapshot name from response: $response"
        return 1
    }

    info "Snapshot created: ${snapshot_name}"

    # 3. Download the snapshot
    local dest_file="${dest_dir}/qdrant_${QDRANT_COLLECTION}_${TIMESTAMP}.snapshot"
    curl -sf -o "$dest_file" \
        "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots/${snapshot_name}" || {
        error "Failed to download snapshot"
        return 1
    }

    local size
    size=$(du -h "$dest_file" | cut -f1)
    info "Qdrant backup saved: ${dest_file} (${size})"

    # 4. Delete the snapshot from Qdrant server (cleanup)
    curl -sf -X DELETE \
        "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots/${snapshot_name}" \
        > /dev/null 2>&1 || true

    # 5. Rotate old backups
    rotate_backups "qdrant_${QDRANT_COLLECTION}_" "$dest_dir"
}

# ── FalkorDB Backup ─────────────────────────────────────────────────────────
backup_falkordb() {
    local dest_dir="${BACKUP_DIR}/falkordb"
    mkdir -p "$dest_dir"

    info "Triggering FalkorDB BGSAVE ..."

    # 1. Trigger background save
    podman exec "$FALKOR_CONTAINER" redis-cli BGSAVE > /dev/null 2>&1 || {
        error "Failed to trigger BGSAVE. Is FalkorDB container '${FALKOR_CONTAINER}' running?"
        return 1
    }

    # 2. Wait for BGSAVE to complete
    info "Waiting for BGSAVE to complete ..."
    local max_wait=30
    for i in $(seq 1 $max_wait); do
        local status
        status=$(podman exec "$FALKOR_CONTAINER" redis-cli LASTSAVE 2>/dev/null) || break
        sleep 1
        local new_status
        new_status=$(podman exec "$FALKOR_CONTAINER" redis-cli LASTSAVE 2>/dev/null) || break
        if [[ "$new_status" != "$status" ]] || [[ "$i" -ge 3 ]]; then
            break
        fi
    done

    # 3. Copy dump.rdb from container
    local dest_file="${dest_dir}/falkordb_${TIMESTAMP}.rdb"
    podman cp "${FALKOR_CONTAINER}:/data/dump.rdb" "$dest_file" || {
        error "Failed to copy dump.rdb from container"
        return 1
    }

    local size
    size=$(du -h "$dest_file" | cut -f1)
    info "FalkorDB backup saved: ${dest_file} (${size})"

    # 4. Rotate old backups
    rotate_backups "falkordb_" "$dest_dir"
}

# ── SQLite Backup ───────────────────────────────────────────────────────────
backup_sqlite() {
    local dest_dir="${BACKUP_DIR}/sqlite"
    mkdir -p "$dest_dir"

    if [[ ! -f "$SQLITE_PATH" ]]; then
        warn "SQLite database not found at ${SQLITE_PATH}, skipping."
        return 0
    fi

    info "Backing up SQLite database ..."

    local dest_file="${dest_dir}/short_term_${TIMESTAMP}.db"

    # Use sqlite3 .backup for a consistent online backup
    sqlite3 "$SQLITE_PATH" ".backup '${dest_file}'" || {
        error "SQLite backup failed"
        return 1
    }

    local size
    size=$(du -h "$dest_file" | cut -f1)
    info "SQLite backup saved: ${dest_file} (${size})"

    # Rotate old backups
    rotate_backups "short_term_" "$dest_dir"
}

# ── Main ────────────────────────────────────────────────────────────────────
main() {
    local target="${1:-all}"

    echo ""
    header "═══════════════════════════════════════════════"
    header "  🗄️  AI Memory Backup – $(date '+%Y-%m-%d %H:%M')"
    header "═══════════════════════════════════════════════"
    echo ""
    info "Backup directory: ${BACKUP_DIR}"
    info "Retention: last ${BACKUP_RETAIN} backups per database"
    echo ""

    local failed=0

    if [[ "$target" == "all" || "$target" == "qdrant" ]]; then
        backup_qdrant || failed=1
        echo ""
    fi

    if [[ "$target" == "all" || "$target" == "falkordb" ]]; then
        backup_falkordb || failed=1
        echo ""
    fi

    if [[ "$target" == "all" || "$target" == "sqlite" ]]; then
        backup_sqlite || failed=1
        echo ""
    fi

    if [[ "$target" != "all" && "$target" != "qdrant" && "$target" != "falkordb" && "$target" != "sqlite" ]]; then
        error "Unknown target: ${target}"
        echo "Usage: bash backup.sh [all|qdrant|falkordb|sqlite]"
        exit 1
    fi

    header "═══════════════════════════════════════════════"
    if [[ "$failed" -eq 0 ]]; then
        info "All backups completed successfully ✅"
    else
        warn "Some backups failed – check output above"
    fi
    header "═══════════════════════════════════════════════"
    echo ""

    exit "$failed"
}

main "$@"
