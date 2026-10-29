#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="$SCRIPT_DIR/sync.cfg"

if [[ ! -f "$CFG" ]]; then
    echo "Error: $CFG not found. Copy sync.cfg.example and fill in your values." >&2
    exit 1
fi
source "$CFG"

REMOTE="${REMOTE_USER}@${REMOTE_HOST}"
CTRL_SOCKET="/tmp/bei_sync_ctl_${REMOTE_USER}"

MODE="${1:-both}"
if [[ "$MODE" != "push" && "$MODE" != "pull" && "$MODE" != "both" ]]; then
    echo "Usage: $0 [push|pull|both]" >&2
    exit 1
fi

# ── SSH ControlMaster ────────────────────────────────────────────────────────
# Opens one authenticated connection (2FA happens here); push and pull reuse it.

open_control_socket() {
    if ssh -O check -S "$CTRL_SOCKET" "$REMOTE" 2>/dev/null; then
        return 0
    fi
    echo "Connecting to $REMOTE (2FA prompt may appear)..."
    ssh -M -S "$CTRL_SOCKET" \
        -o ControlPersist=10m \
        -o StrictHostKeyChecking=accept-new \
        -i "$IDENTITY_FILE" \
        "$REMOTE" "echo '✓ Connection established'" || {
            echo "SSH connection failed." >&2
            exit 1
        }
}

close_control_socket() {
    ssh -S "$CTRL_SOCKET" -O exit "$REMOTE" 2>/dev/null || true
}

trap close_control_socket EXIT

open_control_socket

SSH_CMD="ssh -S $CTRL_SOCKET -i $IDENTITY_FILE"

# ── Push: scripts + source data → server ────────────────────────────────────

do_push() {
    echo ""
    echo "── Push: local → $REMOTE:$REMOTE_DIR"
    rsync -av --progress \
        -e "$SSH_CMD" \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='venv*/' \
        --exclude='final/' \
        --exclude='errors/' \
        --exclude='harmonization/' \
        --exclude='external/' \
        --exclude='claude/' \
        --exclude='*.db' \
        --exclude='*.tar.gz' \
        --exclude='*.tgz' \
        --exclude='*.log' \
        --exclude='.git/' \
        --exclude='sync.cfg' \
        --exclude='mock_ncbi.py' \
        "$SCRIPT_DIR/" \
        "${REMOTE}:${REMOTE_DIR}/"
}

# ── Pull: pipeline outputs ← server ─────────────────────────────────────────

do_pull() {
    echo ""
    echo "── Pull: $REMOTE:$REMOTE_DIR → local"

    local SCP="scp -i $IDENTITY_FILE -o ControlPath=$CTRL_SOCKET"

    # Wipe stale local outputs before pulling fresh copies
    rm -rf "$SCRIPT_DIR/final" "$SCRIPT_DIR/errors/final" "$SCRIPT_DIR/harmonization"
    rm -f  "$SCRIPT_DIR/api_cache.db" "$SCRIPT_DIR/pipeline.log"

    # Directories
    $SCP -r "${REMOTE}:${REMOTE_DIR}/final"         "$SCRIPT_DIR/"
    $SCP -r "${REMOTE}:${REMOTE_DIR}/harmonization" "$SCRIPT_DIR/" 2>/dev/null || true
    $SCP -r "${REMOTE}:${REMOTE_DIR}/errors/final"  "$SCRIPT_DIR/errors/" 2>/dev/null || true

    # Flat files
    $SCP "${REMOTE}:${REMOTE_DIR}/api_cache.db"  "$SCRIPT_DIR/"
    $SCP "${REMOTE}:${REMOTE_DIR}/pipeline.log"  "$SCRIPT_DIR/" 2>/dev/null || true
}

# ── Run ──────────────────────────────────────────────────────────────────────

[[ "$MODE" == "push" || "$MODE" == "both" ]] && do_push
[[ "$MODE" == "pull" || "$MODE" == "both" ]] && do_pull

echo ""
echo "Done."
