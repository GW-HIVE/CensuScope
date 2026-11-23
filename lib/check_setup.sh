#!/bin/bash

set -uo pipefail

# Checks that everything a CensuScope run needs is in place, without sampling
# or aligning anything and without an input sample. Reports the user the run
# would write as, required tools, taxonomy.db, BLAST databases, and whether
# the output directory is writable. Nothing is written.
#
# Usage: check_setup.sh [blast-db-prefix]
#   With no prefix, every BLAST database found under the data directory
#   (CENSUSCOPE_DATADIR, default /app/blastdb) is checked.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

DATA_DIR="${CENSUSCOPE_DATADIR:-/app/blastdb}"
TAXONOMY_DB="$DATA_DIR/taxonomy.db"
OUTPUT_DIR="$REPO_DIR/temp_dirs"
DB_PREFIX="${1:-}"

problems=0
ok()   { echo "  OK       $*"; }
fail() { echo "  PROBLEM  $*"; problems=$((problems + 1)); }

echo "CensuScope setup check (no computation is run)"
echo ""
echo "Running as uid $(id -u), gid $(id -g)"
if [[ "$(id -u)" -eq 0 ]]; then
    echo "  Note: output files would be owned by root."
    echo "        Pass --user \"\$(id -u):\$(id -g)\" to docker run."
fi

echo ""
echo "Tools"
for tool in python3 blastn blastdbcmd seqtk sqlite3 awk grep; do
    if path="$(command -v "$tool")"; then
        ok "$tool ($path)"
    else
        fail "$tool not found"
    fi
done

echo ""
echo "Taxonomy database ($TAXONOMY_DB)"
if [[ -r "$TAXONOMY_DB" ]]; then
    tables="$(sqlite3 -readonly "$TAXONOMY_DB" ".tables" 2>&1)"
    for table in accession_taxid nodes names; do
        if grep -qw "$table" <<< "$tables"; then
            ok "table $table"
        else
            fail "table $table missing"
        fi
    done
else
    fail "taxonomy.db not found or not readable"
fi

echo ""
echo "BLAST database"
prefixes=()
if [[ -n "$DB_PREFIX" ]]; then
    prefixes=("$DB_PREFIX")
else
    # Single-volume databases have <prefix>.nin; multi-volume ones (e.g. nt)
    # have <prefix>.nal plus <prefix>.00.nin, <prefix>.01.nin, ...
    while IFS= read -r prefix; do
        prefixes+=("$prefix")
    done < <(find "$DATA_DIR" \( -name '*.nal' -o -name '*.nin' \) 2>/dev/null \
                 | sed -E 's/(\.[0-9]+)?\.n(al|in)$//' | sort -u)
fi

if [[ ${#prefixes[@]} -eq 0 ]]; then
    fail "no BLAST database files (.nin/.nal) found under $DATA_DIR"
fi
for prefix in ${prefixes[@]+"${prefixes[@]}"}; do
    if info="$(blastdbcmd -db "$prefix" -info 2>&1)"; then
        ok "$prefix: $(grep -m1 "sequences;" <<< "$info" | xargs)"
    else
        fail "$prefix could not be opened by blastdbcmd"
    fi
done

echo ""
echo "Output directory ($OUTPUT_DIR)"
if [[ -d "$OUTPUT_DIR" && -w "$OUTPUT_DIR" ]]; then
    ok "writable by uid $(id -u)"
else
    fail "missing or not writable by uid $(id -u); mount it with -v <dir>:/app/temp_dirs"
fi

echo ""
if [[ "$problems" -eq 0 ]]; then
    echo "All checks passed. Ready to run."
    exit 0
fi
echo "$problems problem(s) found."
exit 1
