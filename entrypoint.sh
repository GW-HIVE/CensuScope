#!/bin/bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "${1:-}" in
    build-taxonomy)
        # Download NCBI taxonomy data and build taxonomy.db into the mounted
        # volume at /app/blastdb (or CENSUSCOPE_DATADIR if overridden).
        shift
        export CENSUSCOPE_DATADIR="${CENSUSCOPE_DATADIR:-/app/blastdb}"
        mkdir -p "$CENSUSCOPE_DATADIR"
        echo "Downloading taxonomy data to $CENSUSCOPE_DATADIR/CensuScopeDB/ ..."
        "$SCRIPT_DIR/lib/download_data.sh" "$@"
        echo "Building taxonomy.db ..."
        "$SCRIPT_DIR/lib/build_database.sh"
        ;;

    build-blast)
        # Build a nucleotide BLAST database from a FASTA file.
        # Usage: build-blast <fasta-file> <db-output-prefix>
        # Example: build-blast /app/blastdb/reference.fasta /app/blastdb/reference
        shift
        FASTA="${1:-}"
        DBOUT="${2:-}"
        if [[ -z "$FASTA" || -z "$DBOUT" ]]; then
            echo "Usage: build-blast <fasta-file> <db-output-prefix>" >&2
            exit 1
        fi
        exec makeblastdb -in "$FASTA" -dbtype nucl -parse_seqids -out "$DBOUT"
        ;;

    "")
        echo "Usage: $(basename "$0") <command> [options]" >&2
        echo "" >&2
        echo "Commands:" >&2
        echo "  build-taxonomy [--force]               Download NCBI data and build taxonomy.db" >&2
        echo "  build-blast <fasta> <db-prefix>        Build a BLAST nucleotide database" >&2
        echo "  <censuscope args>                      Run CensuScope directly" >&2
        echo "" >&2
        echo "Environment:" >&2
        echo "  CENSUSCOPE_DATADIR   Override the output directory for build-taxonomy" >&2
        echo "                       (default: /app/blastdb)" >&2
        exit 1
        ;;

    *)
        exec python "$SCRIPT_DIR/lib/censuscope.py" "$@"
        ;;
esac
