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

## Create a non-root user
# RUN useradd -ms /bin/bash appuser
# USER appuser
WORKDIR /app

## Download NCBI Taxonomy Data
# RUN mkdir CensuScopeDB
# RUN curl -o CensuScopeDB/nucl_gb.accession2taxid.gz \
#     ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz

# RUN curl -o CensuScopeDB/nucl_wgs.accession2taxid.EXTRA.gz \
#     ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.EXTRA.gz

# RUN curl -o CensuScopeDB/nucl_wgs.accession2taxid.gz \
#     ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz

# RUN curl -o CensuScopeDB/new_taxdump.tar.gz \
#     ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz 

# RUN tar -xzf CensuScopeDB/new_taxdump.tar.gz -C CensuScopeDB 

# RUN chown -R appuser:appuser CensuScopeDB 

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

## Default Command: ITERATIONS, etc., should be passed as environment variables via docker run or docker-compose.yml
CMD ["python", "lib/censuscope.py", "--iterations", "$ITERATIONS", "--sample_size", "$SAMPLE_SIZE", "--tax-depth", "$TAXDEPTH", "--query_path", "$QUERYPATH", "--database", "$DATABASE"]
