# Dockerfile

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

RUN useradd -ms /bin/bash appuser
USER appuser
WORKDIR /app

RUN mkdir raw_data

RUN curl -o /app/raw_data/nucl_gb.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz

RUN curl -o /app/raw_data/nucl_wgs.accession2taxid.EXTRA.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.EXTRA.gz

RUN curl -o /app/raw_data/nucl_wgs.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz

RUN curl -o /app/raw_data/new_taxdump.tar.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz 

RUN tar -xzf /app/raw_data/new_taxdump.tar.gz -C /app/raw_data 

RUN chown -R appuser:appuser /app/raw_data 

COPY requirements.txt requirements.txt
COPY lib ./lib

RUN lib/nucleotide-db.sh raw_data/ taxonomy.db
RUN lib/add-nodes.sh raw_data/nodes.dmp taxonomy.db
RUN lib/add-names.sh raw_data/names.dmp taxonomy.db
RUN lib/add-hosts.sh raw_data/host.dmp taxonomy.db

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "lib/censuscope.py", "--iterations", "$ITERATIONS", "--sample_size", "$SAMPLE_SIZE", "--tax-depth", "$TAXDEPTH", "--query_path", "$QUERYPATH", "--database", "$DATABASE"]