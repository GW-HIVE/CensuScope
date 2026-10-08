# CensuScope

CensuScope is a tool for rapid taxonomic profiling of metagenomic NGS data using census-based sampling and BLAST-based alignment. It supports local CLI execution and containerized execution via Docker.

## Quick Start (Docker)

Pull the latest image:

```bash
docker pull ghcr.io/gw-hive/censuscope:2.1.0
```

Run against your FASTQ file and BLAST database:

```bash
docker run \
  -v /path/to/blast_db:/app/blastdb \
  -v /path/to/inputs:/app/inputs \
  -v /path/to/outputs:/app/temp_dirs \
  ghcr.io/gw-hive/censuscope:2.1.0 \
  python lib/censuscope.py \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/query.fastq \
  --database /app/blastdb/<BLASTDB>
```

Output is written to `/path/to/outputs`.

## Documentation

- [Architecture](docs/architecture.md)
- [Taxonomy database](docs/taxonomy.md)
- [CLI deployment](docs/deployment/localDeployment.md)
- [Docker deployment](docs/deployment/dockerDeployment.md)
- [Pull and run (Docker Compose)](docs/deployment/docker_pull.md)
- [Output files](docs/output.md)
- [Development](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)
