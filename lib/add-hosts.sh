#!/bin/bash

set -Eeuo pipefail

case $# in
    2)
        hostFile="$1"
        dbfile="$2"
        ;;
    *) echo "Usage: $(basename "$0") host-file db-file" >&2; exit 1;;
esac

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT INT TERM

# There are some lines in the host.dmp file that end with a trailing
# comma. Clean that up as well as removing TABs.
cut -f1-2 -d\| < "$hostFile" | tr -d '\011' | sed -e 's/,$//' > "$tmp"

sqlite3 "$dbfile" <<EOT

DROP TABLE IF EXISTS hosts;

CREATE TABLE hosts (
    taxid INTEGER NOT NULL,
    hosts VARCHAR NOT NULL
);

.separator '|'
.import "$tmp" hosts

CREATE UNIQUE INDEX hosts_taxid_idx ON hosts(taxid);
EOT
