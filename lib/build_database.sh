#!/bin/bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

# CENSUSCOPE_DATADIR controls where source files are read from and where
# taxonomy.db is written. Defaults to the repo root for local use; set by
# the Docker entrypoint to the mounted volume.
DATA_DIR="${CENSUSCOPE_DATADIR:-$REPO_DIR}"

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=1 ;;
        *) echo "Usage: $(basename "$0") [--force]" >&2; exit 1 ;;
    esac
done

TAXONOMY_DB="$DATA_DIR/taxonomy.db"

# Skip rebuild if taxonomy.db is newer than all source files
if [[ "$FORCE" -eq 0 && -f "$TAXONOMY_DB" ]]; then
    NEEDS_REBUILD=0
    for f in "$DATA_DIR/CensuScopeDB/"*.gz "$DATA_DIR/CensuScopeDB/"*.dmp; do
        if [[ -f "$f" && "$f" -nt "$TAXONOMY_DB" ]]; then
            NEEDS_REBUILD=1
            break
        fi
    done
    if [[ "$NEEDS_REBUILD" -eq 0 ]]; then
        echo "taxonomy.db is up to date. Use --force to rebuild."
        exit 0
    fi
fi

# nodes, names, and host live inside new_taxdump.tar.gz; extract if needed.
if [[ ! -f "$DATA_DIR/CensuScopeDB/nodes.dmp" || \
      ! -f "$DATA_DIR/CensuScopeDB/names.dmp" || \
      ! -f "$DATA_DIR/CensuScopeDB/host.dmp" ]]; then
    echo "Extracting new_taxdump.tar.gz..."
    tar -xzf "$DATA_DIR/CensuScopeDB/new_taxdump.tar.gz" \
        -C "$DATA_DIR/CensuScopeDB" nodes.dmp names.dmp host.dmp
fi

echo "Start building database: $(date)"

./lib/nucleotide-db.sh "$DATA_DIR/CensuScopeDB/" "$TAXONOMY_DB"
./lib/add-nodes.sh "$DATA_DIR/CensuScopeDB/nodes.dmp" "$TAXONOMY_DB"
./lib/add-names.sh "$DATA_DIR/CensuScopeDB/names.dmp" "$TAXONOMY_DB"
cp "$TAXONOMY_DB" "$DATA_DIR/temp.db"
./lib/add-hosts.sh "$DATA_DIR/CensuScopeDB/host.dmp" "$DATA_DIR/temp.db"
mv "$DATA_DIR/temp.db" "$TAXONOMY_DB"

echo "Finished building database: $(date)"
echo "taxonomy.db written to: $TAXONOMY_DB"
