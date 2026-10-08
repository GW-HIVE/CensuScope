#!/bin/bash

# Convenience wrapper for running CensuScope via Docker.
# Update the paths and arguments below before running:
#
#   blastdb/   — directory containing your BLAST database files AND taxonomy.db
#   inputs/    — directory containing your input FASTQ or FASTA file
#   temp_dirs/ — directory where CensuScope writes its output (created if absent)
#
# Arguments to adjust:
#   --iterations    number of sampling iterations
#   --sample-size   reads per iteration
#   --tax-depth     kingdom | phylum | class | order | family | genus | species
#   --query_path    path to your input file inside the container (/app/inputs/...)
#   --database      path to your BLAST database prefix inside the container (/app/blastdb/...)

mkdir -p temp_dirs

docker run \
  -v "$(pwd)/blastdb:/app/blastdb" \
  -v "$(pwd)/inputs:/app/inputs" \
  -v "$(pwd)/temp_dirs:/app/temp_dirs" \
  censuscope \
  python lib/censuscope.py \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/QUERY.FILE \
  --database /app/blastdb/BLASTDB_PREFIX
