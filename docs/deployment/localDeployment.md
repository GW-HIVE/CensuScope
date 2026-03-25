# CensuScope – CLI Usage Guide

This document describes how to run **CensuScope from the command line**, starting from raw inputs and building all required reference data locally.

This guide covers:
- BLAST installation
- Creating a BLAST database
- Building the reduced taxonomy database
- Running CensuScope via CLI
- Understanding outputs

This workflow is intended for developers, power users, and operators who want full control over inputs and reference data.

---

## Overview

CensuScope performs rapid taxonomic profiling of metagenomic NGS data using:
- census-based read sampling
- BLAST-based alignment
- hierarchical aggregation using NCBI taxonomy

CensuScope is **stochastic by design**. Repeated runs with identical inputs may yield slightly different results due to random sampling of reads.

---

## System Requirements

### Operating System
- Linux or macOS (recommended)
- Windows via WSL is possible but not officially supported

### Software Dependencies
- Python ≥ 3.9
- BLAST+ (ncbi-blast+)
- SQLite ≥ 3.35
- seqtk
- curl, tar, awk, sed (standard UNIX tools)

---

## Installing BLAST+

### Linux (Debian/Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y ncbi-blast+
```

### macOS (Homebrew)
```bash
brew install blast
```

Verify installation:
```bash
blastn -version
```

---

## Creating a BLAST Database

CensuScope requires a nucleotide BLAST database built from FASTA files.

### Input
- One or more FASTA files containing reference sequences

Example:
```bash
reference.fasta
```

### Build the BLAST database
```bash
makeblastdb \
  -in reference.fasta \
  -dbtype nucl \
  -parse_seqids \
  -out blast_db/reference
```

This will produce files such as:
```text
reference.nsq
reference.nin
reference.nhr
```

### Notes
- `-parse_seqids` is recommended so BLAST outputs taxonomic identifiers when available
- Large databases may take significant time and disk space (aprox 8x th input file)

---

## Building the Taxonomy Database

CensuScope uses a **reduced taxonomy database** derived from NCBI.

Only two files are required:
- `nodes.dmp`
- `names.dmp`

### Download and extract the NCBI taxonomy dump
See [`taxdump_readme.txt`](https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_readme.txt) for an explanation of these files. These are used to populate the taxonomy DB with the scientific names and the coorisponding taxonomic nodes.

Create the `raw_data` directory:
```bash
mkdir -p raw_data
```

Download the `new_taxdump.tar`:
```bash
curl -o raw_data/new_taxdump.tar.gz \
  https://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz
```

Extract the dump files:
```bash
tar -xzf raw_data/new_taxdump.tar.gz -C raw_data
```

### Download and extract the NCBI accession2taxid mapping files:
See the [`README](https://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/README) for an explanation of these files. This current implementation of CensuScope only uses the LIVE nucleotide sequence records. It is possible to extend the taxonomy DB to include protein sequences or the DEAD sequences, but that significantly increases the DB size and is only usefull if the reference BLASTDB contains protein sequences or depreciated nucleotide sequences. 

Download the `nucl_wgs.accession2taxid.gz`:
```bash
curl -o raw_data/nucl_wgs.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz
```

Download the `nucl_gb.accession2taxid.gz`:
```bash
curl -o raw_data/nucl_gb.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz
```

Download the `nucl_wgs.accession2taxid.EXTRA.gz`:
```bash
curl -o raw_data/nucl_wgs.accession2taxid.EXTRA.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.EXTRA.gz
```

### Build the reduced taxonomy database 
The `nucleotide-db.sh` script will read the three `accession2taxid` files downloaded and create the `accession_taxid` table in `taxonomy.db` (this will take a while).

```bash
sh lib/nucleotide-db.sh raw_data/ taxonomy.db
```

The `add-names.sh` script will read the three `accession2taxid` files downloaded and create the `names` table in `taxonomy.db`.
```bash
sh lib/add-names.sh raw_data/names.dmp taxonomy.db
```

The `add-nodes.sh` script will read the three `accession2taxid` files downloaded and create the `nodes` table in `taxonomy.db`.
```bash
sh lib/add-nodes.sh raw_data/nodes.dmp taxonomy.db
```

### Validate the database
```bash
sqlite3 taxonomy.db <<EOF
.tables
SELECT COUNT(*) FROM nodes;
SELECT COUNT(*) FROM names;
EOF
```

Expected:
- Both tables present
- Row counts on the order of millions
- One name per taxid, or `SELECT COUNT(*) FROM nodes` <= `SELECT COUNT(*) FROM names`

---

## Running CensuScope via CLI

### Input files
- FASTQ or FASTA file containing sequencing reads
- BLAST database
- taxonomy.db

Example directory layout:
```text
blast_db/
taxonomy.db
input.fastq
```

### Basic invocation
```bash
python lib/censuscope.py \
  --input input.fastq \
  --blastdb blast_db/reference \
  --taxonomy taxonomy.db
```

### Common options
```text
--iterations     Number of sampling iterations
--sample-size    Reads sampled per iteration
--threads        Number of BLAST threads
--output-dir     Output directory
```

Refer to `--help` for full option list:
```bash
python lib/censuscope.py --help
```

---

## Output Files

CensuScope produces structured output suitable for downstream analysis.

Typical outputs include:
- `taxonomy_table.tsv` – aggregated taxonomic counts
- `tax_tree.json` – hierarchical taxonomy tree
- `censuscope.log` – execution log

Output location is controlled via CLI options.

---

## Performance Notes

- Runtime scales with:
  - BLAST database size
  - sample size
  - number of iterations
- Taxonomy DB lookups are fast due to reduced schema
- SQLite is sufficient for taxonomy operations

---

## Reproducibility Notes

CensuScope uses random sampling by design.

To reduce variability:
- increase sample size
- increase iteration count

Exact reproducibility is not guaranteed and is not a design goal.

---

## Troubleshooting

### BLAST not found
```text
blastn: command not found
```
Ensure BLAST+ is installed and on your PATH.

---

### Taxonomy lookup failures
- Ensure `taxonomy.db` contains both `nodes` and `names`
- Ensure taxids in BLAST output exist in the taxonomy DB

---

### Slow performance
- Reduce sample size
- Reduce iteration count
- Use fewer BLAST threads if I/O-bound

---

## Summary

This CLI workflow provides full control over:
- reference data
- taxonomy version
- execution parameters

For containerized workflows, see Docker documentation in `docs/deployment/`.
