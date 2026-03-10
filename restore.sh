#!/usr/bin/env bash
# ============================================================================
# restore.sh – Restore Qdrant, FalkorDB or SQLite from backup
# ============================================================================
# Usage:
#   bash restore.sh qdrant    <file.snapshot>    # Restore Qdrant
#   bash restore.sh falkordb  <file.rdb>         # Restore FalkorDB
#   bash restore.sh sqlite    <file.db>          # Restore SQLite
#   bash restore.sh --latest  all                # Restore latest of each
#   bash restore.sh --latest  qdrant             # Restore latest Qdrant
#
# Configuration is loaded from .env.
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

QDRANT_HOST="${QDRANT_HOST:-127.0.0.1}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
QDRANT_COLLECTION="${QDRANT_COLLECTION:-openclaw_memory}"

FALKOR_CONTAINER="${FALKOR_CONTAINER:-falkordb}"
FALKOR_STORAGE="${FALKOR_STORAGE:-/home/clawdi/.falkor_storage}"

SQLITE_PATH="${SQLITE_PATH:-$HOME/.openclaw/short_term.db}"
SQLITE_PATH="${SQLITE_PATH/#\~/$HOME}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[RESTORE]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}    $*"; }
error() { echo -e "${RED}[ERROR]${NC}   $*"; }
header(){ echo -e "${CYAN}$*${NC}"; }

# ── Helper: find latest backup ──────────────────────────────────────────────
find_latest() {
    local dir="$1"
    local pattern="$2"
    find "$dir" -maxdepth 1 -name "${pattern}" -type f 2>/dev/null \
        | sort \
        | tail -n 1
}

# ── Helper: confirm action ──────────────────────────────────────────────────
confirm() {
    local msg="$1"
    echo -e "${YELLOW}⚠️  ${msg}${NC}"
    read -r -p "Continue? [y/N] " answer
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        info "Aborted."
        return 1
    fi
}

# ── Qdrant Restore ──────────────────────────────────────────────────────────
restore_qdrant() {
    local snapshot_file="$1"

    if [[ ! -f "$snapshot_file" ]]; then
        error "Snapshot file not found: ${snapshot_file}"
        return 1
    fi

    info "Restoring Qdrant collection '${QDRANT_COLLECTION}' from: ${snapshot_file}"
    confirm "This will REPLACE all data in the '${QDRANT_COLLECTION}' collection." || return 1

    # 1. Pre-restore backup
    info "Creating pre-restore backup ..."
    local pre_backup_dir="${BACKUP_DIR}/qdrant"
    mkdir -p "$pre_backup_dir"
    local pre_response
    pre_response=$(curl -sf -X POST \
        "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots" \
        -H "Content-Type: application/json" 2>/dev/null) || true
    if [[ -n "$pre_response" ]]; then
        local pre_snap_name
        pre_snap_name=$(echo "$pre_response" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['name'])" 2>/dev/null) || true
        if [[ -n "${pre_snap_name:-}" ]]; then
            curl -sf -o "${pre_backup_dir}/qdrant_${QDRANT_COLLECTION}_pre_restore_${TIMESTAMP}.snapshot" \
                "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots/${pre_snap_name}" 2>/dev/null || true
            curl -sf -X DELETE \
                "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots/${pre_snap_name}" \
                > /dev/null 2>&1 || true
            info "Pre-restore backup saved"
        fi
    fi

    # 2. Upload and recover from snapshot file
    info "Uploading snapshot to Qdrant ..."

    # Use the recover endpoint with the local file
    # First, copy snapshot to a temp location Qdrant can access, or upload via API
    local abs_path
    abs_path="$(cd "$(dirname "$snapshot_file")" && pwd)/$(basename "$snapshot_file")"

    curl -sf -X PUT \
        "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${QDRANT_COLLECTION}/snapshots/recover" \
        -H "Content-Type: application/json" \
        -d "{\"location\": \"file://${abs_path}\"}" || {
        error "Failed to restore Qdrant snapshot"
        return 1
    }

    info "Qdrant collection '${QDRANT_COLLECTION}' restored successfully ✅"
}

# ── FalkorDB Restore ────────────────────────────────────────────────────────
restore_falkordb() {
    local rdb_file="$1"

    if [[ ! -f "$rdb_file" ]]; then
        error "RDB file not found: ${rdb_file}"
        return 1
    fi

    info "Restoring FalkorDB from: ${rdb_file}"
    confirm "This will STOP the FalkorDB container, replace its data, and restart it." || return 1

    # 1. Pre-restore backup
    info "Creating pre-restore backup ..."
    local pre_backup_dir="${BACKUP_DIR}/falkordb"
    mkdir -p "$pre_backup_dir"
    podman exec "$FALKOR_CONTAINER" redis-cli BGSAVE > /dev/null 2>&1 || true
    sleep 2
    podman cp "${FALKOR_CONTAINER}:/data/dump.rdb" \
        "${pre_backup_dir}/falkordb_pre_restore_${TIMESTAMP}.rdb" 2>/dev/null || true
    info "Pre-restore backup saved"

    # 2. Stop container
    info "Stopping FalkorDB container ..."
    podman stop "$FALKOR_CONTAINER" || {
        error "Failed to stop FalkorDB container"
        return 1
    }

    # 3. Replace dump.rdb in the storage volume
    info "Replacing database file ..."
    cp "$rdb_file" "${FALKOR_STORAGE}/dump.rdb" || {
        error "Failed to copy RDB file to ${FALKOR_STORAGE}"
        podman start "$FALKOR_CONTAINER"
        return 1
    }

    # 4. Start container
    info "Starting FalkorDB container ..."
    podman start "$FALKOR_CONTAINER" || {
        error "Failed to start FalkorDB container"
        return 1
    }

    # 5. Wait for readiness
    info "Waiting for FalkorDB ..."
    for i in $(seq 1 10); do
        if podman exec "$FALKOR_CONTAINER" redis-cli PING 2>/dev/null | grep -q PONG; then
            break
        fi
        sleep 1
    done

    info "FalkorDB restored successfully ✅"
}

# ── SQLite Restore ──────────────────────────────────────────────────────────
restore_sqlite() {
    local db_file="$1"

    if [[ ! -f "$db_file" ]]; then
        error "Database file not found: ${db_file}"
        return 1
    fi

    info "Restoring SQLite from: ${db_file}"
    confirm "This will REPLACE the SQLite database at ${SQLITE_PATH}." || return 1

    # 1. Pre-restore backup
    if [[ -f "$SQLITE_PATH" ]]; then
        info "Creating pre-restore backup ..."
        local pre_backup_dir="${BACKUP_DIR}/sqlite"
        mkdir -p "$pre_backup_dir"
        cp "$SQLITE_PATH" "${pre_backup_dir}/short_term_pre_restore_${TIMESTAMP}.db"
        info "Pre-restore backup saved"
    fi

    # 2. Verify the backup file is valid SQLite
    if ! sqlite3 "$db_file" "SELECT 1;" > /dev/null 2>&1; then
        error "File is not a valid SQLite database: ${db_file}"
        return 1
    fi

    # 3. Replace database
    mkdir -p "$(dirname "$SQLITE_PATH")"
    cp "$db_file" "$SQLITE_PATH" || {
        error "Failed to copy database file"
        return 1
    }

    info "SQLite database restored successfully ✅"
    warn "If memory_watcher is running, restart it to pick up the new database."
}

# ── Main ────────────────────────────────────────────────────────────────────
usage() {
    echo "Usage:"
    echo "  bash restore.sh <db>       <backup-file>   # Restore from specific file"
    echo "  bash restore.sh --latest   <db|all>         # Restore from latest backup"
    echo ""
    echo "Databases: qdrant, falkordb, sqlite, all"
    echo ""
    echo "Examples:"
    echo "  bash restore.sh qdrant    ~/.openclaw/backups/qdrant/qdrant_openclaw_memory_20260310.snapshot"
    echo "  bash restore.sh --latest  all"
    echo "  bash restore.sh --latest  sqlite"
}

restore_latest() {
    local target="$1"
    local failed=0

    if [[ "$target" == "all" || "$target" == "qdrant" ]]; then
        local latest
        latest=$(find_latest "${BACKUP_DIR}/qdrant" "qdrant_${QDRANT_COLLECTION}_*.snapshot")
        if [[ -n "$latest" ]]; then
            info "Latest Qdrant backup: $(basename "$latest")"
            restore_qdrant "$latest" || failed=1
        else
            warn "No Qdrant backups found in ${BACKUP_DIR}/qdrant/"
            [[ "$target" == "qdrant" ]] && failed=1
        fi
        echo ""
    fi

    if [[ "$target" == "all" || "$target" == "falkordb" ]]; then
        local latest
        latest=$(find_latest "${BACKUP_DIR}/falkordb" "falkordb_*.rdb")
        if [[ -n "$latest" ]]; then
            info "Latest FalkorDB backup: $(basename "$latest")"
            restore_falkordb "$latest" || failed=1
        else
            warn "No FalkorDB backups found in ${BACKUP_DIR}/falkordb/"
            [[ "$target" == "falkordb" ]] && failed=1
        fi
        echo ""
    fi

    if [[ "$target" == "all" || "$target" == "sqlite" ]]; then
        local latest
        latest=$(find_latest "${BACKUP_DIR}/sqlite" "short_term_*.db")
        if [[ -n "$latest" ]]; then
            info "Latest SQLite backup: $(basename "$latest")"
            restore_sqlite "$latest" || failed=1
        else
            warn "No SQLite backups found in ${BACKUP_DIR}/sqlite/"
            [[ "$target" == "sqlite" ]] && failed=1
        fi
        echo ""
    fi

    return "$failed"
}

main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    echo ""
    header "═══════════════════════════════════════════════"
    header "  🔄 AI Memory Restore – $(date '+%Y-%m-%d %H:%M')"
    header "═══════════════════════════════════════════════"
    echo ""

    local failed=0

    if [[ "$1" == "--latest" ]]; then
        local target="${2:-all}"
        restore_latest "$target" || failed=1
    elif [[ "$1" == "--help" || "$1" == "-h" ]]; then
        usage
        exit 0
    else
        local db="$1"
        local file="${2:-}"

        if [[ -z "$file" ]]; then
            error "Backup file path required"
            echo ""
            usage
            exit 1
        fi

        case "$db" in
            qdrant)   restore_qdrant "$file"   || failed=1 ;;
            falkordb) restore_falkordb "$file"  || failed=1 ;;
            sqlite)   restore_sqlite "$file"    || failed=1 ;;
            *)
                error "Unknown database: ${db}"
                usage
                exit 1
                ;;
        esac
    fi

    echo ""
    header "═══════════════════════════════════════════════"
    if [[ "$failed" -eq 0 ]]; then
        info "Restore completed successfully ✅"
    else
        error "Restore failed – check output above"
    fi
    header "═══════════════════════════════════════════════"
    echo ""

    exit "$failed"
}

main "$@"
