#!/bin/bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=1 ;;
        *) echo "Usage: $(basename "$0") [--force]" >&2; exit 1 ;;
    esac
done

# Skip rebuild if taxonomy.db is newer than all source files
if [[ "$FORCE" -eq 0 && -f "taxonomy.db" ]]; then
    NEEDS_REBUILD=0
    for f in CensuScopeDB/*.gz CensuScopeDB/*.dmp; do
        if [[ -f "$f" && "$f" -nt "taxonomy.db" ]]; then
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
if [[ ! -f CensuScopeDB/nodes.dmp || ! -f CensuScopeDB/names.dmp || ! -f CensuScopeDB/host.dmp ]]; then
    echo "Extracting new_taxdump.tar.gz..."
    tar -xzf CensuScopeDB/new_taxdump.tar.gz -C CensuScopeDB nodes.dmp names.dmp host.dmp
fi

echo "Start building database: $(date)"

./lib/nucleotide-db.sh CensuScopeDB/ taxonomy.db
./lib/add-nodes.sh CensuScopeDB/nodes.dmp taxonomy.db
./lib/add-names.sh CensuScopeDB/names.dmp taxonomy.db
cp taxonomy.db temp.db
./lib/add-hosts.sh CensuScopeDB/host.dmp temp.db
mv temp.db taxonomy.db

echo "Finished building database: $(date)"
