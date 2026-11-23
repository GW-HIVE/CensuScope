# CensuScope Docker Deployment

## Contents
- [Requirements](#requirements)
- [Build the image](#build-the-image)
- [Prepare reference data](#prepare-reference-data)
- [Run CensuScope](#run-censuscope)
- [Command line options](#command-line-options)
- [Output Results](#output-results)
- [Reproducibility Notes](#reproducibility-notes)

## Requirements

- [Docker](https://docs.docker.com/engine/install/) (Docker Desktop on macOS/Windows also works).
- Enough disk for the reference data. `taxonomy.db` is about 7 GB, the NCBI downloads used to build it are about 11 GB, and a BLAST database can need anywhere from a few GB to hundreds of GB.

You do **not** need Python, BLAST+, or seqtk on the host. They are all inside the image.

---

## Build the image

```bash
git clone https://github.com/GW-HIVE/CensuScope.git
cd CensuScope
docker build -t censuscope .
```

The build starts from the public `python:3.14-slim-trixie` image (pinned by digest in the `Dockerfile`) and installs BLAST+, seqtk, and SQLite from the Debian archive. No pre-built CensuScope image is involved.

Tag the image with a version (`censuscope:v1.0`) or your initials if you keep several builds around, and use the same tag in the commands below.

Reference data is **not** copied into the image. It is mounted at runtime (see below), so you do not need to put databases in the repository before building.

---

## Prepare reference data

> **Batch builds:** `build_reference_data.sh` in the repository root runs both steps below for every FASTA in `../databases/input/<BaseDB>/`. It writes to `../databases/output/<BaseDB>/`, skips databases that are already built, and logs each step. Run `./build_reference_data.sh --help` for details. To log CPU and RAM load during a build or grid search, wrap it in `./run_monitored.py build -- ...` or `./run_monitored.py grid -- ...`.

All reference data lives in one host directory that is mounted at `/app/blastdb` in the container. These examples use `./blastdb`:

```bash
mkdir -p blastdb inputs temp_dirs
```

Pass `--user "$(id -u):$(id -g)"` to every `docker run` so that the files the container creates are owned by you. Do not `chmod 777` the directories.

### taxonomy.db

The `build-taxonomy` command downloads the NCBI taxonomy dumps into `blastdb/CensuScopeDB/` and builds `blastdb/taxonomy.db`:

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(pwd)/blastdb:/app/blastdb" \
  censuscope build-taxonomy
```

Re-running it only re-downloads files that changed. Pass `--force` to re-download everything. See [taxonomydb.md](taxonomydb.md) for the schema and how often to refresh it.

Once `taxonomy.db` is built, you can delete `blastdb/CensuScopeDB/` to reclaim space.

### BLAST database

Put your reference FASTA (e.g. `slimNT.fa`) in `blastdb/`, then build the database:

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$(pwd)/blastdb:/app/blastdb" \
  censuscope build-blast /app/blastdb/slimNT.fa /app/blastdb/slimNT
```

The second argument is the database **prefix**. `makeblastdb` writes `slimNT.nsq`, `slimNT.nin`, `slimNT.nhr`, and related files next to it, and `/app/blastdb/slimNT` is what you pass to `--database`. See [blast_database.md](blast_database.md) for choosing a reference set.

If you already have a BLAST database built elsewhere, copy its files into `blastdb/` instead.

---

## Run CensuScope

The image's entrypoint runs CensuScope, so CensuScope options go directly after the image name. Do **not** add `python lib/censuscope.py`.

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
  --database /app/blastdb/slimNT
```

- `blastdb/` must contain `taxonomy.db` and the BLAST database files.
- `inputs/` holds your FASTQ/FASTA query. The repository ships `inputs/sample_input.fastq` for a test run.
- `temp_dirs/` receives a timestamped folder per run.

[`run_docker.sh`](../run_docker.sh) in the repository root is a template for this command.

**Concurrent runs:** output folders are named to the second. If you start several runs at the same moment, give each its own `temp_dirs` mount.

### Entrypoint commands

| Command | Purpose |
|---|---|
| `build-taxonomy [--force]` | Download NCBI taxonomy data and build `taxonomy.db` in `/app/blastdb` |
| `build-blast <fasta> <db-prefix>` | Run `makeblastdb -dbtype nucl -parse_seqids` |
| *(anything else)* | Passed straight to CensuScope |

Running the image with no arguments prints this usage.

---

## Command line options

```text
usage: censuscope [options]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -i ITERATIONS, --iterations ITERATIONS
                        The number of sample iterations to perform
  -s SAMPLE_SIZE, --sample-size SAMPLE_SIZE
                        The number of reads to sample for each iteration
  -t {kingdom,phylum,class,order,family,genus,species}, --tax-depth ...
                        The taxonomy depth to report in the final results
  -q QUERY_PATH, --query_path QUERY_PATH
                        Input file name. Accepted formats: FASTA (.fasta, .fa) or FASTQ (.fastq, .fq)
  -d DATABASE, --database DATABASE
                        BLAST nucleotide database path (e.g. /path/to/nt or /path/to/slimNT)
  --taxonomy-db TAXONOMY_DB
                        Path to taxonomy.db (default: /app/blastdb/taxonomy.db)
```

---

## Output Results
Each run creates a timestamped folder under the `temp_dirs/` directory you mounted. 
```
cd temp_dirs/
```
An example of the newly created results directories:
```
2026_03_30_18.04.20
2026_03_31_17.18.01
2026_04_01_16.47.48
```
cd into your newest directory from your  most recent CensuScope run. Inside there will be 4 directories:
```
- blastn
- inputs
- random_samples
- results
```

### blastn folder
The NCBI Blast alignment results from the random samples can be found in this directory. There is one blast result file for each iteration. 

### inputs folder
This is a temporary folder used to store temporary fastas for the CensuScope computation. This folder should be empty. 

### random_samples folder
The random samples used to perform the CensuScope computation can be found in this directory. The random samples are in FASTA format. There is one random sample file for each iteration. 

### results folder
The main results of the CensuScope computation can be found in this directory. The result files are:
- `taxonomy_table.tsv` – aggregated taxonomic counts
- `tax_tree.json` – hierarchical taxonomy tree
- `censuscope.log` – execution log
- `accession_table.tsv` - accessions and hit count results

The following samples show the expected output format when running CensuScope with `sample_input.fastq`. Exact values will vary depending on your BLAST database and run parameters.

A sample of the `accession_table.tsv` when running with `sample_input.fastq` is:
```
Accession	Total Hits	Iterations Present	Average Hits
CM001951	6	1	0.02
CM001943	4	1	0.0133
LC492974	7	1	0.0233
CM014356	1	1	0.0033
CM001948	5	1	0.0167
CM014351	1	1	0.0033
CM001952	5	1	0.0167
```

A sample of the `taxonomy_table.tsv` when running with `sample_input.fastq` is:
```
Taxid	Name	Percentage	Total Hits	Iterations Present	Full Lineage
60711	Chlorocebus sabaeus	0.3333	100	1	Eukaryota; Opisthokonta; Metazoa; Eumetazoa; Bilateria; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Dipnotetrapodomorpha; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Euarchontoglires; Primates; Haplorrhini; Simiiformes; Cercopithecidae; Chlorocebus; Chlorocebus sabaeus
9544	Macaca mulatta	0.07	21	1	Eukaryota; Opisthokonta; Metazoa; Eumetazoa; Bilateria; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Dipnotetrapodomorpha; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Euarchontoglires; Primates; Haplorrhini; Simiiformes; Cercopithecidae; Macaca; Macaca mulatta
9598	Pan troglodytes	0.0033	1	1	Eukaryota; Opisthokonta; Metazoa; Eumetazoa; Bilateria; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Dipnotetrapodomorpha; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Euarchontoglires; Primates; Haplorrhini; Simiiformes; Hominidae; Pan; Pan troglodytes
10116	Rattus norvegicus	0.0	0	0	Eukaryota; Opisthokonta; Metazoa; Eumetazoa; Bilateria; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Dipnotetrapodomorpha; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Euarchontoglires; Rodentia; Rattus; Rattus norvegicus
10090	Mus musculus	0.0	0	0	Eukaryota; Opisthokonta; Metazoa; Eumetazoa; Bilateria; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Dipnotetrapodomorpha; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Euarchontoglires; Rodentia; Mus; Mus musculus
9612	Canis lupus	0.0	0	0	Eukaryota; Opisthokonta; Metazoa; Eumetazoa; Bilateria; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Dipnotetrapodomorpha; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Laurasiatheria; Carnivora; Canidae; Canis; Canis lupus
```

A sample of the `tax_tree.json` when running with `sample_input.fastq` is:
```
{
    "0": {
	"taxid": 0,
        "name": "unmatched",
        "rank": null,
        "children": null,
        "accessions": [
            "LC492974",
            "BQXJ01000001",
            "BSCU01000028"
        ]
    },
    "2759": {
	"taxid": 2759,
        "parent": 131567,
        "name": "Eukaryota",
        "rank": "domain",
        "children": {
            "33154": {
                "taxid": 33154,
                "parent": 2759,
                "name": "Opisthokonta",
                "rank": "clade",
                "children": {
                    "33208": {
                        "taxid": 33208,
                        "parent": 33154,
                        "name": "Metazoa",
                        "rank": "kingdom",
                        "children": {
                            "6072": {
                                "taxid": 6072,
                                "parent": 33208,
                                "name": "Eumetazoa",
                                "rank": "clade",

                ...
```

---

### Reproducibility Notes

CensuScope uses random sampling by design.

To reduce variability:
- increase sample size
- increase iteration count

Exact reproducibility is not guaranteed and is not a design goal.
