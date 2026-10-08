#!/bin/bash

# Convenience wrapper for running CensuScope via Docker.
#
# ── First-time setup ──────────────────────────────────────────────────────
#
# 1. Build taxonomy.db (one-time, ~30–60 min depending on connection).
#    Downloads NCBI data and builds the database inside the container,
#    writing taxonomy.db to ./blastdb/ on the host:
#
#   mkdir -p blastdb
#   docker run -v "$(pwd)/blastdb:/app/blastdb" censuscope build-taxonomy
#
# 2. Build a BLAST database from your reference FASTA (one-time):
#
#   docker run -v "$(pwd)/blastdb:/app/blastdb" censuscope \
#     build-blast /app/blastdb/reference.fasta /app/blastdb/reference
#
# ── Run ───────────────────────────────────────────────────────────────────
# Update paths and arguments below, then run this script.
#
#   blastdb/   — directory containing BLAST database files and taxonomy.db
#   inputs/    — directory containing your input FASTQ or FASTA file
#   temp_dirs/ — directory where CensuScope writes its output

mkdir -p temp_dirs

docker run \
  -v "$(pwd)/blastdb:/app/blastdb" \
  -v "$(pwd)/inputs:/app/inputs" \
  -v "$(pwd)/temp_dirs:/app/temp_dirs" \
  censuscope \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/QUERY.FILE \
  --database /app/blastdb/BLASTDB_PREFIX
