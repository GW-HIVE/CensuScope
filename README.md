# CensuScope
CensuScope is a tool for rapid taxonomic profiling of NGS metagenomic data
using census-based sampling and BLAST-based alignment. It supports local CLI execution, containerized execution via Docker builds, or exicution via a prebuilt Docker image.

## Table of Contents
1.  [Overview](#overview)
2.  [System Architecture](#system-architecture)
3.  [Taxonomy Database](#taxonomy-database)
4.  [Installation and Requirements](#installation-and-requirements)
5.  [Deployment](#deployment)
      - [Build from CLI](#build-from-cli) (scratch)
      - [Build with Docker](#build-with-docker)
      - [Pull and run Docker image](#pull-and-run-docker-image)
6.  [Output Files](#output-files)
7.  [Development](#development)
    - [Testing](#testing)
    - [Validation](#validation)
    - [Contribution](#contribution)
8.  [Troubleshooting](#troubleshooting)


## Overview
CensuScope is a tool for estimating the taxonomic composition of metagenomic sequencing data using census-based sampling and alignment. Instead of analyzing every read in a dataset, CensuScope repeatedly samples subsets of reads and aligns them against reference databases to infer which organisms are present and at what relative levels.

This approach is intentionally **stochastic**. Reads are selected at random from the input FASTQ file, and alignment results depend on which reads are sampled in a given run. As a result, two runs with the same inputs can produce different outputs. This behavior is expected and is a core feature of the method rather than a limitation. CensuScope is designed to produce statistically meaningful estimates through aggregation and repeated analysis, not bit-for-bit reproducible results.

The original [CensuScope algorithm](https://pmc.ncbi.nlm.nih.gov/articles/PMC4218995) was implemented as a UNIX-based pipeline, with its core logic captured in the [unix.php](lib/unix.php) script included in this repository. The results reported in the original CensuScope publication were generated using that implementation. The current Python version of CensuScope is a direct continuation of that work, preserving the same sampling-based logic while updating the execution model to support modern workflows.

In the current implementation, alignment results are combined across sampled reads to produce taxonomic summaries at species or higher taxonomic levels. Individual read assignments are not treated as definitive classifications. Instead, taxonomic profiles emerge from aggregation across many probabilistic observations.

The Python-based CensuScope engine improves portability, supports containerized execution, and standardizes output formats, while maintaining the original algorithmic behavior and assumptions of the census-based approach.

## System Architecture
CensuScope is buit with a clear separation between static infrastructure, dynamic inputs, and generated outputs. This separation supports flexible execution (local or containerized), minimizes runtime assumptions, and makes the behavior of the system explicit.

At a high level, a CensuScope run consists of:

1. Randomly sampling reads from an input sequencing file
2. Aligning sampled reads against a nucleotide BLAST database
3. Mapping alignments to taxonomic identifiers
4. Aggregating alignment evidence into taxonomic summaries
### Core components
#### **FASTQ input** (dynamic, user-provided)
- User-provided sequencing data in FASTQ format
- Treated as read-only input
- May vary between runs and users
- Randomly sampled during execution

The FASTQ file is the primary source of variability between runs.

#### **BLAST database** (external, static, user-provided)
- User-provided nucleotide BLAST database
- Built externally using standard BLAST tooling
- Not modified by CensuScope
- May be shared across multiple runs and analyses

CensuScope treats the BLAST database as a fixed reference against which sampled reads are aligned.

#### **Taxonomy database** (internal, static)
- SQLite database derived from the NCBI taxonomy
- Built ahead of time and treated as immutable at runtime
- Provides taxonomic hierarchy and canonical names
- Uses a reduced schema tailored to CensuScope’s lookup and aggregation needs

In containerized deployments, a prebuilt taxonomy database is shipped with the image

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

### Architectural Principles
The system architecture is guided by the following principles:

- **Stochastic estimation**:
    Each run produces a sampling-based estimate; variability across runs is expected.

- **Separation of concerns**: 
    Reference data, runtime inputs, and outputs are clearly separated.

- **Portability**: 
    The same architecture supports local execution and containerized deployment.

- **Minimal runtime assumptions**:
    All required reference data is resolved before execution begins.

This architecture underpins the deployment and execution modes described later in this document.

## Taxonomy Database
CensuScope uses a reduced taxonomy database derived from the [NCBI taxonomy](). The taxonomy database is treated as **static reference infrastructure** and is not modified at runtime.

The purpose of the taxonomy database in CensuScope is to provide:
- taxonomic hierarchy (parent–child relationships), and
- a single canonical scientific name for each taxonomic identifier.

Unlike a full NCBI taxonomy representation, CensuScope intentionally uses a simplified schema. Each taxonomic identifier (taxid) is associated with **exactly one canonical scientific name**.

This design reflects how taxonomy is used in CensuScope:
- taxonomy is used for lookup and aggregation, not name disambiguation,
- synonyms and alternate name classes are not required at runtime,
- taxonomic inference is performed through aggregation of alignment evidence rather than per-read classification.

The taxonomy database includes the following tables:
- **nodes**: taxonomic hierarchy (taxid, parent taxid, rank)
- **names**: canonical scientific names (taxid, name)

**Build and Lifecycle**

The taxonomy database must be built **prior to run time**, not during execution. Once created, it is treated as immutable.

In containerized deployments, the official CensuScope Docker image ships with a **prebuilt taxonomy database** that conforms to this reduced schema. In local or custom deployments, users may build their own taxonomy database following the documented process.

**Relationship to Stochastic Execution**

The taxonomy database itself is static and deterministic. However, because CensuScope relies on stochastic sampling of sequencing reads, the way taxonomy is exercised during a run is probabilistic. Differences in sampled reads can lead to different taxonomic summaries across runs, even when the same taxonomy database is used.

**Provenance and Documentation**

The reduced taxonomy schema used by CensuScope is a deliberate engineering choice informed by the original CensuScope methodology and its reference implementation. It preserves the taxonomic structure required for aggregation while simplifying runtime assumptions and deployment.

Detailed instructions for building and validating the taxonomy database are provided separately.

See: docs/processes/01_taxonomy_db.md

## Installation and Requirements

### CLI requirements
#### Operating System
- Linux or macOS (recommended)
- Windows via WSL is possible but not officially supported
#### Software Dependencies
- Python ≥ 3.9
- BLAST+ (ncbi-blast+)
- SQLite ≥ 3.35
- seqtk
- curl, tar, awk, sed (standard UNIX tools)

### Docker requirements
- Docker

## Deployment
CensuScope supports three officially supported deployment and execution modes. Each mode uses the same underlying architecture and execution logic, differing only in how the software and reference data are prepared and invoked.

All deployment modes assume that reference data (BLAST database and taxonomy database) are prepared ahead of execution and treated as read-only during runtime.

**Notes on execution behavior**
- CensuScope execution is stochastic by design.
- Repeated runs with identical inputs may produce different outputs.
- Differences between deployment modes affect environment setup, not algorithmic behavior.

Users should select a deployment mode based on their operational needs rather than expectations of output reproducibility.

### **Supported Deployment Modes**:
#### Build from CLI
**Intended for:**
Developers, advanced users, and researchers who want full control over the execution environment.

In this mode, CensuScope is built and run directly from source using a local Python environment. All dependencies, reference databases, and runtime configuration are managed by the user.

This approach provides maximum flexibility for development, debugging, and experimentation, at the cost of additional setup.

See: [docs/deployment/localDeployment.md](docs/deployment/localDeployment.md)

#### Build with Docker
Intended for:
Developers, CI systems, and users who want a controlled and portable execution environment.

In this mode, a Docker image is built locally from the CensuScope source code. The image encapsulates the runtime environment and application logic, while external reference data (such as BLAST databases) may be mounted at runtime.

This approach ensures consistency across environments while still allowing customization during the build process.

See: docs/processes/03_docker_build_and_run.md

#### Pull and run Docker image
**Intended for:**
End users and operators who want to run CensuScope with minimal setup.

In this mode, a prebuilt Docker image is pulled from a container registry and executed directly. The official image ships with a prebuilt taxonomy database that conforms to the CensuScope schema contract. Users provide input data and reference BLAST databases at runtime via mounted volumes.

This is the fastest way to get started and requires no local build steps.

See: docs/processes/04_pull_and_run.md

## Output Files
Describe:

What files are produced

Where they go

Which are stable outputs vs intermediates

This is essential for users integrating CensuScope downstream.
## Development
### Testing 
Brief but explicit:

What is tested

What is not

How to run tests

This ties directly to your “operations want tests” requirement.

    - [Testing](docs/testing.md)
### Validation
### Contribution
## Troubleshooting
Include:

taxonomy.db schema mismatch

missing BLAST DB

Docker volume issues

You already have the raw material for this section from this discussion.

    - [FAQ and trouble shooting](docs/faq.md)

Deployment instructions: 
- [Local deployment](docs/deployment/localDeployment.md) 
- [Docker deployment](docs/deployment/dockerDeployment.md)


