# CensuScope
<img width="150" height="150" alt="scope" src="https://github.com/user-attachments/assets/16a39d8e-29ba-4e53-b677-7ecb4ae1500e" />

CensuScope is a tool for rapid taxonomic profiling of NGS metagenomic data using census-based sampling and BLAST-based alignment. It supports local CLI execution, containerized execution via Docker builds, or exicution via a prebuilt Docker image.

---

## Table of Contents
1.  [Overview](#overview)
2.  [System Architecture](#system-architecture)
3.  [Deployment](#deployment)
4.  [Output Files](#output-files)

## Overview
CensuScope is a tool for estimating the taxonomic composition of metagenomic sequencing data using census-based sampling and alignment. Instead of analyzing every read in a dataset, CensuScope repeatedly samples subsets of reads and aligns them against reference databases to infer which organisms are present and at what relative levels.

This approach is intentionally **stochastic**. Reads are selected at random from the input FASTQ file, and alignment results depend on which reads are sampled in a given run. As a result, two runs with the same inputs can produce different outputs. This behavior is expected and is a core feature of the method rather than a limitation. CensuScope is designed to produce statistically meaningful estimates through aggregation and repeated analysis, not bit-for-bit reproducible results.

The original [CensuScope algorithm](https://pmc.ncbi.nlm.nih.gov/articles/PMC4218995) was implemented as a UNIX-based pipeline, with its core logic captured in the [unix.php](lib/unix.php) script included in this repository. The results reported in the original CensuScope publication were generated using that implementation. The current Python version of CensuScope is a direct continuation of that work, preserving the same sampling-based logic while updating the execution model to support modern workflows.

In the current implementation, alignment results are combined across sampled reads to produce taxonomic summaries at species or higher taxonomic levels. Individual read assignments are not treated as definitive classifications. Instead, taxonomic profiles emerge from aggregation across many probabilistic observations.

The Python-based CensuScope engine improves portability, supports containerized execution, and standardizes output formats, while maintaining the original algorithmic behavior and assumptions of the census-based approach.

---

## System Architecture
CensuScope is buit with a clear separation between static infrastructure, dynamic inputs, and generated outputs. This separation supports flexible execution (local or containerized), minimizes runtime assumptions, and makes the behavior of the system explicit.

At a high level, a CensuScope run consists of:

1. Randomly sampling reads from an input sequencing file
2. Aligning sampled reads against a nucleotide BLAST database
3. Mapping alignments to taxonomic identifiers
4. Aggregating alignment evidence into taxonomic summaries
   
### Core components
#### **FASTQ/A input** (dynamic, user-provided)
- User-provided sequencing data in FASTQ or FASTA format
- Treated as read-only input
- May vary between runs and users
- Randomly sampled during execution

The FASTQ file is the primary source of variability between runs. The code does account for FASTA and converts to FASTQ.

#### **BLAST database** (external, static, user-provided)
- User-provided nucleotide BLAST database
- Built externally using standard BLAST tooling
- Not modified by CensuScope
- May be shared across multiple runs and analyses

CensuScope treats the BLAST database as a fixed reference against which sampled reads are aligned. 
Common database options include:

- **NCBI NT database** (standard, comprehensive)
  - Use NCBI's [FTP BLAST Site](https://ftp.ncbi.nlm.nih.gov/blast/db/) to locate and download BLAST database files, including NT.
- **SlimNT** (curated, reduced database)
  - The GitHub Repo to create or download `slimNT.fa` can be found [here](https://github.com/GW-HIVE/slimNT).
- **Filtered NT** (lab-specific filtered database)
  - The GitHub Repo to create or download `filter_nt.fa` can be found [here](https://github.com/GW-HIVE/filtered_nt).
 
The README [blast_database.md](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/blast_database.md) in the `docs` folder can provide more information and step-by-step directions.

#### **Taxonomy database** (internal, static)
- SQLite database derived from the NCBI taxonomy
- Built ahead of time and treated as immutable at runtime
- Provides taxonomic hierarchy and canonical names
- Uses a reduced schema tailored to CensuScope’s lookup and aggregation needs

The taxonomy.db file needs to be created prior to runtime by the user. See the [taxonomydb.md](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/taxonomydb.md) README in `docs`.

#### CensuScope Engine (Runtime)
- Python-based execution engine
- Responsible for:
    - read sampling
    - BLAST invocation
    - taxonomy lookup
    - aggregation and reporting

The engine is stateless across runs aside from generated outputs. No persistent state is carried between executions.

#### **Output artifacts** (generated per run)
- Per-run output files produced during execution
- May include:
    - taxonomic summary tables
    - lineage representations
    - logs and intermediate artifacts

Outputs are written to a designated output directory and may differ between runs even when inputs are identical.

The [outputs]() are described in the [dockerDeployment.md]() README in `docs`.

---

## Deployment
CensuScope requires two reference resources to be prepared before execution:

1. a taxonomy database (`taxonomy.db`)
2. a nucleotide BLAST database (such as SlimNT, filtered NT, or NCBI NT)

These files are treated as **read-only inputs** during runtime and must be available before running the workflow. Once both databases are prepared, CensuScope can be executed using the Docker deployment guide.

For step-by-step setup instructions for the CensuScope Workflow, follow the documentation in this order:

1. **Build the taxonomy database**  
   See [taxonomydb.md](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/taxonomydb.md)

2. **Prepare or obtain a BLAST database**  
   See [blast_database.md](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/blast_database.md)

3. **Build and run CensuScope with Docker**  
   See [dockerDeployment.md](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/deployment/dockerDeployment.md)

This documentation structure follows the same order as the CensuScope workflow: first prepare the taxonomy reference, then prepare the sequence reference database, and finally run the containerized pipeline.


## Output Files
Describe:

What files are produced

Where they go

Which are stable outputs vs intermediates

This is essential for users integrating CensuScope downstream.
