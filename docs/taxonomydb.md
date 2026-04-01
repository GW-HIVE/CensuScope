# Taxonomy Database

This document describes the taxonomy database used by CensuScope: its purpose, schema, build process, and validation. The taxonomy database is treated as **static reference infrastructure** and is not modified during execution.

CensuScope uses a **reduced taxonomy schema** derived from the NCBI taxonomy. The reduced schema is a deliberate design choice aligned with how taxonomy is used during census-based sampling and aggregation.

---
## Table of Contents
1. [Purpose](#purpose)
2. [Taxonomy DB Schema](#taxonomy-db-schema)
3. [Required NCBI Tables](#required-ncbi-tables)
4. [Build Taxonomy.db File](#build-taxonomydb-file)
5. [Taxonomy.db Validation](#taxonomydb-validation)

---

## Purpose

The taxonomy database provides:

- taxonomic hierarchy (parent–child relationships)
- a single canonical scientific name per taxonomic identifier (`taxid`)

It is used exclusively for:
- mapping BLAST alignments to taxonomic identifiers
- aggregating results across taxonomic ranks
- labeling output tables and lineage structures

The taxonomy database is **not** used for:
- synonym resolution
- name disambiguation
- host association
- per-read classification

---

## Taxonomy DB Schema 

CensuScope intentionally does **not** use the full NCBI taxonomy schema. Only the tables required for hierarchical aggregation and labeling are included.

### Required NCBI Tables

### Source Data

The taxonomy database is derived from the NCBI taxonomy dump files:

- `nodes.dmp`
- `names.dmp`
- `hosts.dmp`

Only records required to populate the reduced schema are extracted. In particular, only rows from `names.dmp` with `name_class == "scientific name"` are used.

#### `nodes`

Stores the taxonomic hierarchy.

| Column        | Type    | Description                          |
|---------------|---------|--------------------------------------|
| taxid         | INTEGER | NCBI taxonomic identifier            |
| parent_taxid  | INTEGER | Parent taxid in the taxonomy tree    |
| rank          | TEXT    | Taxonomic rank (e.g., species, genus)|

Each taxid appears exactly once.

#### `names`

Stores the canonical scientific name for each taxid.

| Column | Type    | Description               |
|-------|---------|---------------------------|
| taxid | INTEGER | NCBI taxonomic identifier |
| name  | TEXT    | Canonical scientific name |

Exactly **one row per taxid** is retained. Only scientific names are included.

---

## Build Taxonomy.db File

### Process Overview

The taxonomy database must be built **prior to runtime** to be used. Because this process can take a significant amount of time, it should be completed well in advance of running the Docker deployment.

At a high level, the build process consists of:

1. Creating a fresh SQLite database
2. Creating the required tables (`nodes`, `names`)
3. Loading taxonomy hierarchy from `nodes.dmp`
4. Loading canonical scientific names from `names.dmp`
5. Validating schema and basic integrity

### Build Scripts

NCBI regularly updates their [FTP Taxonomy file site](https://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/) with minor edits, but we suggest updating your `taxonomy.md` file every 6 months to a year. 
The following scripts are used to build the taxonomy database:

- `lib/download_data.sh`  
  This script downloads the required NCBI taxonomy and accession-to-taxid files needed to build the taxonomy.db database. It retrieves the latest versions from the NCBI FTP site. 
- `lib/build_database.sh`  
  This script constructs the taxonomy.db database from the downloaded NCBI data files. It ensures required taxonomy files are extracted and then runs a series of steps to populate the database with accession, taxonomy structure, names, and host mappings.
  - `build_database.sh` script also utilizes the shell scripts, which can be found in /lib, `add-nodes.sh`, `add-names.sh`, and `add-hosts.sh` to process and load taxonomy hierarchy, scientific names, and host metadata into the database.


Scripts related to host metadata or other unused taxonomy features are considered legacy and are not part of the supported build process.

---

## Taxonomy.db Validation

After building the taxonomy database, the following checks should be performed.

### Schema Validation

```sql
.tables
PRAGMA table_info(nodes);
PRAGMA table_info(names);
```

Only the expected tables and columns should be present.

---

### Row Counts

```sql
SELECT COUNT(*) FROM nodes;
SELECT COUNT(*) FROM names;
```

Both tables should contain non-zero rows. In a full NCBI build, counts will be on the order of millions.

---

### Join Integrity

```sql
SELECT COUNT(*)
FROM nodes n
LEFT JOIN names na ON n.taxid = na.taxid
WHERE na.name IS NULL;
```

The number of missing names should be minimal.

---

### CensuScope Compatibility Check

The following query mirrors the join pattern used by CensuScope:

```sql
SELECT n.taxid, na.name, n.rank, n.parent_taxid
FROM nodes n
JOIN names na ON n.taxid = na.taxid
LIMIT 10;
```

If this query succeeds, the taxonomy database is compatible with CensuScope.

---

## Relationship to Stochastic Execution

The taxonomy database itself is static and deterministic. However, CensuScope execution is stochastic due to random sampling of sequencing reads. As a result, the same taxonomy database may produce different output summaries across runs.

This behavior is expected and reflects the census-based design of the method.

---

## Usage in Docker Images

The official CensuScope Docker image ships with a **prebuilt taxonomy database** that conforms to this document. Users running the image do not need to build taxonomy locally.

Custom builds may substitute a different taxonomy database, provided it adheres to the same reduced schema contract.

---

## Change Policy

Changes to the taxonomy schema or build process must be reflected in:

- this document
- the build scripts in `lib/`
- the Docker image build process
- the main `README.md`

This document is the authoritative reference for the CensuScope taxonomy database.
