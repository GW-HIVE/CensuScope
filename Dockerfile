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

WORKDIR /app
COPY requirements.txt requirements.txt
COPY lib ./lib

## Python Setup
RUN pip install --no-cache-dir -r requirements.txt

## Default Command: ITERATIONS, etc., should be passed as environment variables via docker run or docker-compose.yml
CMD ["python", "lib/censuscope.py", "--iterations", "$ITERATIONS", "--sample_size", "$SAMPLE_SIZE", "--tax-depth", "$TAXDEPTH", "--query_path", "$QUERYPATH", "--database", "$DATABASE"]
