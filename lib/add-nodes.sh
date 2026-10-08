#!/bin/bash

set -Eeuo pipefail

echo ""
echo "--- running add-nodes.sh at $(date)"

case $# in
    2)
        nodeFile="$1"
        dbfile="$2"
        ;;
    *) echo "Usage: $(basename "$0") node-file db-file" >&2; exit 1;;
esac

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT INT TERM

# The sed command adjusts the 'no rank' value of Riboviria to have the correct
# 'realm' value, and all other 'no rank' ranks get changed to '-'. The '-'
# value is relied upon in CensuScope's taxonomy traversal code.
cut -f1-3 -d\| < "$nodeFile" | tr -d '\011' | \
    sed -e 's/^2559587|10239|no rank$/2559587|10239|realm/' \
        -e 's/|no rank$/|-/' > "$tmp"
echo "   nodeFile is: $nodeFile"

sqlite3 "$dbfile" <<EOT

DROP TABLE IF EXISTS nodes;

CREATE TABLE nodes (
    taxid INTEGER NOT NULL,
    parent_taxid INTEGER NOT NULL,
    rank VARCHAR NOT NULL
);

.separator '|'
.import "$tmp" nodes

CREATE UNIQUE INDEX nodes_taxid_idx ON nodes(taxid);
CREATE INDEX nodes_parent_idx ON nodes(parent_taxid);
EOT

echo "*** Done add-nodes.sh at $(date)"
