#!/bin/bash
set -Eeuo pipefail

case $# in
    2)
        namesFile="$1"
        dbfile="$2"
        ;;
    *)
        echo "Usage: $(basename "$0") names.dmp taxonomy.db" >&2
        exit 1
        ;;
esac

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT INT TERM

# NCBI names.dmp format:
# tax_id | name_txt | unique_name | name_class |
#
# Retain ONLY scientific names:
# taxid | name

cut -f1-4 -d\| < "$namesFile" \
  | tr -d '\011' \
  | awk -F\| '$4 == "scientific name" { printf "%s|%s\n", $1, $2 }' \
  > "$tmp"

sqlite3 "$dbfile" <<EOF
PRAGMA journal_mode = OFF;
PRAGMA synchronous = OFF;
PRAGMA temp_store = MEMORY;
PRAGMA cache_size = -1000000;

BEGIN;

DROP TABLE IF EXISTS names;
DROP TABLE IF EXISTS names_tmp;

CREATE TABLE names_tmp (
    taxid INTEGER NOT NULL,
    name  TEXT    NOT NULL
);

.separator '|'
.import $tmp names_tmp

-- Enforce exactly one scientific name per taxid
CREATE TABLE names (
    taxid INTEGER PRIMARY KEY,
    name  TEXT NOT NULL
);

INSERT INTO names (taxid, name)
SELECT taxid, name
FROM names_tmp
GROUP BY taxid;

DROP TABLE names_tmp;

COMMIT;
EOF
