#!/bin/bash

set -Eeuo pipefail

# Downloads the files needed to build taxonomy.db. These files are updated
# monthly by NCBI — re-run this script to refresh the data.
# This script only needs to be run once before building the database.
# Note: Downloads may take 15-60 minutes depending on your connection.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

mkdir -p CensuScopeDB

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=1 ;;
        *) echo "Usage: $(basename "$0") [--force]" >&2; exit 1 ;;
    esac
done

download_if_changed() {
    local url="$1"
    local dest="$2"

    if [[ "$FORCE" -eq 0 && -f "$dest" ]]; then
        local remote_size
        remote_size=$(curl -sI "$url" | grep -i "^content-length:" | awk '{print $2}' | tr -d '\r')
        local local_size
        local_size=$(wc -c < "$dest")
        if [[ "$remote_size" == "$local_size" ]]; then
            echo "$(basename "$dest"): up to date (${local_size} bytes), skipping"
            return
        fi
        echo "$(basename "$dest"): remote differs (remote=${remote_size}, local=${local_size}), downloading..."
    else
        echo "$(basename "$dest"): downloading..."
    fi

    curl -o "$dest" "$url"
}

BASE_URL="https://ftp.ncbi.nlm.nih.gov/pub/taxonomy"

download_if_changed "${BASE_URL}/accession2taxid/nucl_gb.accession2taxid.gz" \
    "CensuScopeDB/nucl_gb.accession2taxid.gz"
download_if_changed "${BASE_URL}/accession2taxid/nucl_wgs.accession2taxid.EXTRA.gz" \
    "CensuScopeDB/nucl_wgs.accession2taxid.EXTRA.gz"
download_if_changed "${BASE_URL}/accession2taxid/nucl_wgs.accession2taxid.gz" \
    "CensuScopeDB/nucl_wgs.accession2taxid.gz"
download_if_changed "${BASE_URL}/new_taxdump/new_taxdump.tar.gz" \
    "CensuScopeDB/new_taxdump.tar.gz"

echo "Done. Run lib/build_database.sh to build taxonomy.db."
