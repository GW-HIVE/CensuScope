# Dockerfile

## Base Image & System Packages
FROM python:3.10-slim
RUN apt-get update && apt-get install -y \
    wget \
    gcc \
    make \
    curl \
    sqlite3 \
    zlib1g-dev \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install NCBI BLAST+
RUN apt-get update && apt-get install -y ncbi-blast+ \
    && rm -rf /var/lib/apt/lists/*

# Install Seqtk
RUN wget https://github.com/lh3/seqtk/archive/refs/tags/v1.3.tar.gz && \
    tar -xzvf v1.3.tar.gz && \
    cd seqtk-1.3 && \
    make && \
    mv seqtk /usr/local/bin/ && \
    cd .. && \
    rm -rf seqtk-1.3 v1.3.tar.gz

# Running as root: appropriate for single-user workstations and HPC
# (Singularity maps UIDs automatically). For shared Docker environments,
# restore the appuser block below and ensure mounted volumes are readable
# by UID 1000, or pass --user $(id -u):$(id -g) at runtime.
# RUN useradd -ms /bin/bash appuser && mkdir -p /app && chown appuser:appuser /app
# USER appuser
WORKDIR /app

# Create the mount point for the taxonomy/BLAST database directory.
# For KVM2 or air-gapped builds: uncomment COPY to bake the DB into the image.
RUN mkdir -p blastdb
# COPY blastdb /app/blastdb

## taxonomy.db and BLAST database files are provided at runtime via volume mount.
## Run lib/download_data.sh and lib/build_database.sh locally to prepare them.
## See lib/download_data.sh, lib/build_database.sh, and run_docker.sh.

COPY requirements.txt requirements.txt
COPY lib ./lib

## Build the SQLite Database
# RUN lib/nucleotide-db.sh CensuScopeDB/ taxonomy.db && \
#     lib/add-nodes.sh CensuScopeDB/nodes.dmp taxonomy.db && \
#     lib/add-names.sh CensuScopeDB/names.dmp taxonomy.db && \
#     cp taxonomy.db temp.db && \
#     lib/add-hosts.sh CensuScopeDB/host.dmp temp.db && \
#     mv temp.db taxonomy.db

## Python Setup
RUN pip install --no-cache-dir -r requirements.txt

## Default Command: pass arguments via docker run or docker-compose.yml
CMD ["python", "lib/censuscope.py", "--iterations", "$ITERATIONS", "--sample_size", "$SAMPLE_SIZE", "--tax-depth", "$TAXDEPTH", "--query_path", "$QUERYPATH", "--database", "$DATABASE"]
