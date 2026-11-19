# CensuScope container image.
#
# Built from the official Python slim image plus Debian packages: no
# pre-built CensuScope image, no pip, no compilers. CensuScope itself uses
# only the Python standard library.
#
#   docker build -t censuscope .
#
# Base: Python 3.14 on Debian 13 (trixie), pinned by digest so rebuilds get
# the same Python and OS layer. BLAST+/seqtk come from the Debian archive.
# To update the base: `docker pull python:3.14-slim-trixie`, then replace the
# digest with the one from
#   docker inspect --format '{{index .RepoDigests 0}}' python:3.14-slim-trixie
FROM python:3.14-slim-trixie@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

LABEL org.opencontainers.image.title="CensuScope" \
      org.opencontainers.image.description="Census-based metagenomic taxonomic profiling with BLAST" \
      org.opencontainers.image.source="https://github.com/GW-HIVE/CensuScope" \
      org.opencontainers.image.licenses="CC-BY-3.0"

# ncbi-blast+            blastn, makeblastdb
# seqtk                  FASTQ -> FASTA conversion
# sqlite3                taxonomy.db build scripts
# curl, ca-certificates  NCBI downloads for build-taxonomy
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ncbi-blast+ \
        seqtk \
        sqlite3 \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Runs as root by default: appropriate for single-user workstations and HPC
# (Singularity/Apptainer maps UIDs automatically). On shared Docker hosts,
# pass --user "$(id -u):$(id -g)" at runtime so output files are owned by you.
WORKDIR /app

# Mount points: reference data (taxonomy.db + BLAST DB) at /app/blastdb,
# run output at /app/temp_dirs. Sticky world-writable so --user still works
# if a directory is left unmounted.
#
# Air-gapped builds: uncomment the COPY below to bake the reference data
# into the image, and remove blastdb/ from .dockerignore.
RUN mkdir -p blastdb temp_dirs && chmod 1777 blastdb temp_dirs
# COPY blastdb /app/blastdb

COPY lib ./lib
COPY entrypoint.sh ./
RUN chmod 755 entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
