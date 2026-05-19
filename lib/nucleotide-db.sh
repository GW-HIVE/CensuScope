#!/bin/bash

set -Eeuo pipefail

# dbfile is the taxonomy.db file
# nucl_gb is the CensuScopeDB directory that contains:
#   nucl_wgs.accession2taxid.EXTRA.gz
#   nucl_wgs.accession2taxid.gz
#   nucl_gb.accession2taxid.gz

echo "Running with nucleotide-db.sh file at $(date)..."

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

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT INT TERM

echo "Using nucl_gb: $nucl_gb"
echo ""

echo "--- appending nucl_wgs.accession2taxid.EXTRA.gz at $(date)..."
case "${nucl_gb}nucl_wgs.accession2taxid.EXTRA.gz" in
    *.gz)
        gunzip -c < "${nucl_gb}nucl_wgs.accession2taxid.EXTRA.gz" | tail -n +2 | cut -f1,3 > "$tmp"
        ;;
    *)
        tail -n +2 < "${nucl_gb}nucl_wgs.accession2taxid.EXTRA.gz" | cut -f1,3 > "$tmp"
        ;;
esac

wc -l "$tmp"

echo "--- appending nucl_wgs.accession2taxid.gz at $(date)..."
case "${nucl_gb}nucl_wgs.accession2taxid.gz" in
    *.gz)
        gunzip -c < "${nucl_gb}nucl_wgs.accession2taxid.gz" | tail -n +2 | cut -f1,3 >> "$tmp"
        ;;
    *)
        tail -n +2 < "${nucl_gb}nucl_wgs.accession2taxid.gz" | cut -f1,3 >> "$tmp"
        ;;
esac

wc -l "$tmp"

echo "--- appending nucl_gb.accession2taxid.gz at $(date)..."
case "${nucl_gb}nucl_gb.accession2taxid.gz" in
    *.gz)
        gunzip -c < "${nucl_gb}nucl_gb.accession2taxid.gz" | tail -n +2 | cut -f1,3 >> "$tmp"
        ;;
    *)
        tail -n +2 < "${nucl_gb}nucl_gb.accession2taxid.gz" | cut -f1,3 >> "$tmp"
        ;;
esac

wc -l "$tmp"

echo ""
echo "-------- sqlite3 step at $(date) --------"
echo "Using dbfile: $dbfile"

sqlite3 <<EOF
.open $dbfile

CREATE TABLE IF NOT EXISTS accession_taxid (
    accession VARCHAR UNIQUE PRIMARY KEY,
    taxid INTEGER NOT NULL
);

DROP INDEX IF EXISTS accession_taxid_accession_idx;
DROP TABLE IF EXISTS tmp_accession_taxid;

CREATE TEMP TABLE tmp_accession_taxid (
    accession VARCHAR,
    taxid INTEGER
);

.mode tabs
.import $tmp tmp_accession_taxid

INSERT OR IGNORE INTO accession_taxid(accession, taxid)
SELECT accession, taxid
FROM tmp_accession_taxid;

CREATE UNIQUE INDEX accession_taxid_accession_idx ON accession_taxid(accession);

DROP TABLE tmp_accession_taxid;
EOF
