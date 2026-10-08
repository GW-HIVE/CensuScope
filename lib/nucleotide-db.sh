#!/bin/bash

set -Eeuo pipefail

# First argument is the CensuScopeDB directory, containing either:
#   nucl_wgs.accession2taxid.EXTRA  (or .EXTRA.gz)
#   nucl_wgs.accession2taxid        (or .gz)
#   nucl_gb.accession2taxid         (or .gz)
# Second argument is the target taxonomy.db file.

echo "Running nucleotide-db.sh at $(date)..."

case $# in
    2)
        nucl_gb="$1"
        dbfile="$2"
        ;;
    *)
        echo "Usage: $(basename "$0") accession-dir db-file" >&2
        exit 1
        ;;
esac

# Normalize directory path to ensure trailing slash
nucl_gb="${nucl_gb%/}/"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT INT TERM

append_file() {
    local base="$1"
    local mode="$2"

    echo "--- appending ${base} at $(date)..."

    if [[ -f "${nucl_gb}${base}" ]]; then
        echo "    using uncompressed file: ${nucl_gb}${base}"
        if [[ "$mode" == "write" ]]; then
            tail -n +2 < "${nucl_gb}${base}" | cut -f1,3 > "$tmp"
        else
            tail -n +2 < "${nucl_gb}${base}" | cut -f1,3 >> "$tmp"
        fi
    elif [[ -f "${nucl_gb}${base}.gz" ]]; then
        echo "    using gz file: ${nucl_gb}${base}.gz"
        if [[ "$mode" == "write" ]]; then
            gunzip -c < "${nucl_gb}${base}.gz" | tail -n +2 | cut -f1,3 > "$tmp"
        else
            gunzip -c < "${nucl_gb}${base}.gz" | tail -n +2 | cut -f1,3 >> "$tmp"
        fi
    else
        echo "ERROR: could not find ${nucl_gb}${base} or ${nucl_gb}${base}.gz" >&2
        exit 1
    fi

    wc -l "$tmp"
}

echo "Using nucl_gb: $nucl_gb"
echo ""

append_file "nucl_wgs.accession2taxid.EXTRA" "write"
append_file "nucl_wgs.accession2taxid" "append"
append_file "nucl_gb.accession2taxid" "append"

echo ""
echo "-------- sqlite3 step at $(date) --------"
echo "Using dbfile: $dbfile"

sqlite3 "$dbfile" <<EOF

DROP TABLE IF EXISTS accession_taxid;
DROP TABLE IF EXISTS tmp_accession_taxid;

CREATE TABLE accession_taxid (
    accession VARCHAR UNIQUE PRIMARY KEY,
    taxid INTEGER NOT NULL
);

CREATE TEMP TABLE tmp_accession_taxid (
    accession VARCHAR,
    taxid INTEGER
);
DROP INDEX IF EXISTS accession_taxid_accession_idx;
DROP TABLE IF EXISTS tmp_accession_taxid;

CREATE TEMP TABLE tmp_accession_taxid (
    accession VARCHAR,
    taxid INTEGER
);

.mode tabs
.import "$tmp" tmp_accession_taxid

INSERT OR IGNORE INTO accession_taxid(accession, taxid)
SELECT accession, taxid
FROM tmp_accession_taxid;

CREATE UNIQUE INDEX accession_taxid_accession_idx ON accession_taxid(accession);

DROP TABLE tmp_accession_taxid;
EOF

echo "*** Done nucleotide-db.sh at $(date)"
