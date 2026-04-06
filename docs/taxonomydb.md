# Taxonomy Database

This document describes the taxonomy database used by CensuScope: its purpose, schema, build process, and validation. The taxonomy database is treated as **static reference infrastructure** and is not modified during execution.

CensuScope uses a **reduced taxonomy schema** derived from the NCBI taxonomy. The reduced schema is a deliberate design choice aligned with how taxonomy is used during census-based sampling and aggregation.

---
## Table of Contents
1. [Purpose](#purpose)
2. [Taxonomy DB Schema](#taxonomy-db-schema)
3. [Required NCBI Tables](#required-ncbi-tables)
4. [Build Taxonomy.db File](#-build-taxonomydb-file) -> Step-by-step Instructions
5. [Taxonomy.db Validation](#taxonomydb-validation)
6. [Next Steps](#next-steps)

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

## 🧬 Build Taxonomy.db File

### Process Overview

The taxonomy database must be built **prior to runtime** to be used. Because this process can take a significant amount of time, it should be completed well in advance of running the Docker deployment.

At a high level, the build process consists of:

1. Creating a fresh SQLite database
2. Creating the required tables (`nodes`, `names`, `hosts`)
3. Loading taxonomy hierarchy from `nodes.dmp`
4. Loading canonical scientific names from `names.dmp`
5. Loading host metadata from `host.dmp`
6. Validating schema and basic integrity

### Build Scripts

NCBI regularly updates their [FTP Taxonomy file site](https://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/) with minor edits monthly, but we suggest updating your `taxonomy.md` file every _6 months to a year_. Since their updates are mostly minor and given the amount of time it takes to build the database, it is unnecessary to build a new one each time.

The following scripts are used to build the taxonomy database:
- `lib/download_data.sh`  
  This script downloads the required NCBI taxonomy and accession-to-taxid files needed to build the taxonomy.db database. It retrieves the latest versions from the NCBI FTP site. 
- `lib/build_database.sh`  
  This script constructs the taxonomy.db database from the downloaded NCBI data files. It ensures required taxonomy files are extracted and then runs a series of steps to populate the database with accession, taxonomy structure, names, and host mappings.
  - `build_database.sh` script also utilizes the shell scripts, which can be found in /lib, `add-nodes.sh`, `add-names.sh`, and `add-hosts.sh` to process and load taxonomy hierarchy, scientific names, and host metadata into the database.

Note: Scripts related to host metadata or other unused taxonomy features are considered legacy and are not part of the supported build process.

---

### 🧬 Running the Build Scripts

First, clone the CensuScope repository:
```
git clone https://github.com/GW-HIVE/CensuScope/
```

Navigate to the CensuScope directory
```
cd CensuScope
```

To download the required NCBI data files, run:
```
./lib/download_data.sh
```

- This step may take approximately **15–60 minutes** depending on network speed.

The downloaded files will be placed in the `CensuScopeDB/` directory. Verify that the following files are present:

- `nucl_gb.accession2taxid.gz`
- `nucl_wgs.accession2taxid.EXTRA.gz`
- `nucl_wgs.accession2taxid.gz`
- `new_taxdump.tar.gz`
  

Once all files are confirmed, build the taxonomy database:
```
./lib/build_database.sh
```
- This step can take approximately **3–6 hours**. Plan accordingly.

Once the `build_database.sh` script has finished running, verify that the `taxonomy.db` file has been created in the root `CensuScope/` directory:
```
ls -lh taxonomy.db
```

You should see a non-empty file (typically several GB in size). If the file is missing or empty, the build process may have failed and should be reviewed before proceeding.

Note: The taxonomy.db file is in SQLite format and therefore not human-readable.

---

## Taxonomy.db Validation

After building the taxonomy database, the following checks should be performed.

### Schema Validation

```sql
.tables
PRAGMA table_info(nodes);
PRAGMA table_info(names);
```
- Only the expected tables and columns should be present.

### Row Counts

```sql
SELECT COUNT(*) FROM nodes;
SELECT COUNT(*) FROM names;
```
- Both tables should contain non-zero rows. In a full NCBI build, counts will be on the order of millions.

### Join Integrity

```sql
SELECT COUNT(*)
FROM nodes n
LEFT JOIN names na ON n.taxid = na.taxid
WHERE na.name IS NULL;
```
- The number of missing names should be minimal.

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
## Next Steps

Once the `taxonomy.db` database has been successfully built and validated, the next steps depend on your setup:

### If you do not yet have a BLAST database:
- Follow the instructions in the [BLAST database README](https://github.com/GW-HIVE/CensuScope/blob/main/docs/blast_database.md) to download and build the required database files.

### If you already have both a BLAST database and `taxonomy.db`:
- Proceed to the [CensuScope Docker Deployment README](https://github.com/GW-HIVE/CensuScope/blob/main/docs/dockerDeployment.md) for instructions on building and running the container.
