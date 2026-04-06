# Documentation on Deployment and Files

This directory contains documentation for deploying and running CensuScope, along with the core reference resources required for execution. Because multiple components are needed (such as reference databases and infrastructure dependencies), the documentation is organized into separate files, each describing a specific part of the system.

This README serves as an **overview** and **table of contents** for the documentation in this folder. Each linked document explains what the resource is, how it is created or obtained, and how it is used within the CensuScope workflow.

---

## 🦒 Taxonomy Database Documentation

This document, [taxonomydb.md](https://github.com/GW-HIVE/CensuScope/blob/main/docs/taxonomydb.md), describes the taxonomy database used by CensuScope.

- The taxonomy database provides the **taxonomic hierarchy and naming structure** used to interpret results.
- It is treated as **static reference infrastructure** and is not modified during execution.
- A valid `taxonomy.db` file is required for running CensuScope.
- The document explains how the database is built from the NCBI taxonomy dump, how to build it yourself, and how it is used for lineage mapping and result aggregation.

---

## 💻 BLAST Database Documentation

This document, [blast_database.md](https://github.com/GW-HIVE/CensuScope/blob/main/docs/blast_database.md), describes the BLAST database used by CensuScope.

- The BLAST database is the **reference sequence database** used to align sequencing reads.
- It is treated as **external, static input data** and must be prepared before execution.
- The document explains how to obtain or build a BLAST database (e.g., NT, SlimNT, filtered NT).
- It includes step-by-step instructions for creating a BLAST database using `makeblastdb`.
- Additional sections describe how the BLAST database interacts with `taxonomy.db` during taxonomic classification.

---

## 📤 Docker Deployment Guide (Primary)

This document, [dockerDeployment.md](https://github.com/GW-HIVE/CensuScope/blob/main/docs/dockerDeployment.md), is the primary guide for running CensuScope in a Docker container.

- Explains how to build and run the CensuScope Docker image.
- Describes required inputs, including:
  - FASTQ input files
  - BLAST database
  - taxonomy database (`taxonomy.db`)
- Provides commands for mounting input, database, and output directories.

---

## 🧬 How These Components Work Together

CensuScope relies on three core components:

- **FASTQ Input (dynamic)**  
  Sequencing reads provided by the user for each run.

- **BLAST Database (static)**  
  Reference sequences used for alignment.

- **Taxonomy Database (`taxonomy.db`) (static)**  
  Provides taxonomic structure for interpreting results.

Together, these components enable:
- alignment of reads → via BLAST database  
- mapping to taxonomy → via `taxonomy.db`  
- aggregation and reporting → via CensuScope  

All reference components must be prepared **before execution** and are treated as **read-only inputs** during runtime.
