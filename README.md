# CensuScope

CensuScope is a tool for rapid taxonomic profiling of metagenomic NGS data using census-based sampling and BLAST-based alignment. It runs in a Docker container that bundles BLAST+, seqtk, and the Python engine.

## Quick Start (Docker)

### 1. Build the image

```bash
git clone https://github.com/GW-HIVE/CensuScope.git
cd CensuScope
docker build -t censuscope .
```

### 2. Prepare reference data (one-time)

CensuScope needs two reference databases in one host directory, which is mounted at `/app/blastdb`:

- `taxonomy.db`, built from NCBI taxonomy dumps. The download is large and the build takes a while.
- A nucleotide BLAST database built from your reference FASTA.

```bash
mkdir -p blastdb inputs temp_dirs

# Download NCBI taxonomy data and build blastdb/taxonomy.db
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(pwd)/blastdb:/app/blastdb" \
  censuscope build-taxonomy

# Build a BLAST database from a FASTA you have placed in blastdb/
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(pwd)/blastdb:/app/blastdb" \
  censuscope build-blast /app/blastdb/reference.fasta /app/blastdb/reference
```

See [docs/taxonomydb.md](docs/taxonomydb.md) and [docs/blast_database.md](docs/blast_database.md) for details.

### 3. Run

The container's entrypoint runs CensuScope directly, so pass CensuScope options right after the image name:

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(pwd)/blastdb:/app/blastdb:ro" \
  -v "$(pwd)/inputs:/app/inputs:ro" \
  -v "$(pwd)/temp_dirs:/app/temp_dirs" \
  censuscope \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/sample_input.fastq \
  --database /app/blastdb/reference
```

`--database` takes the BLAST database **prefix** (the `-out` value given to `build-blast`), not a file name.

Results are written to a timestamped folder under `temp_dirs/`. See [docs/output.md](docs/output.md).

[`run_docker.sh`](run_docker.sh) is a template wrapper for the same command.

## Documentation

- [Docker deployment guide](docs/dockerDeployment.md)
- [Architecture](docs/architecture.md)
- [Taxonomy database](docs/taxonomydb.md)
- [BLAST database](docs/blast_database.md)
- [Output files](docs/output.md)
- [Development](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

See [LICENSE](LICENSE).
