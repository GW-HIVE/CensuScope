# CensuScope Core Library

This directory contains the core scripts and infrastructure used by CensuScope for database preparation, sequence alignment, taxonomy mapping, and result aggregation.

The scripts in this directory support:
- taxonomy database construction
- BLAST database preparation
- metagenomic profiling execution
- intermediate BLAST result processing
- lineage aggregation and reporting

---

## Main Runtime Script

### censuscope.py

Primary CensuScope execution script.

Responsible for:
- FASTA/FASTQ validation
- random read sampling
- BLAST execution
- taxonomy mapping
- lineage aggregation
- report generation

This is the main script executed during standard CensuScope runs.

---

## Database Construction Scripts

### build_database.sh

Wrapper script used to build the CensuScope taxonomy database infrastructure.

Coordinates:
- accession mapping import
- taxonomy dump processing
- database population

---

### nucleotide-db.sh

Builds the `accession_taxid` table from NCBI accession2taxid files.

Responsible for importing accession-to-taxonomy mappings into SQLite.

---

### add-nodes.sh

Imports NCBI taxonomy node hierarchy into the `nodes` table.

Provides parent-child taxonomy structure used for lineage traversal.

---

### add-names.sh

Imports scientific names into the `names` table.

Used for converting TaxIDs into human-readable taxonomy names.

---

### add-hosts.sh

Imports host-related taxonomy information into the `hosts` table.

Used for host association metadata where applicable.

---

## Database Download Scripts

### download_data.sh

Downloads required NCBI taxonomy and accession mapping resources used for database construction.

Typical resources include:
- taxonomy dump files
- accession2taxid files
- host mapping files

---

## BLAST Processing Utilities

### process_blast_file_chunk.py

Processes intermediate BLAST output chunks generated during CensuScope execution.

Used for:
- parsing BLAST output
- accession extraction
- taxonomy aggregation support

---

## Supporting Files

### __init__.py

Marks the `lib` directory as a Python package.

Currently contains no runtime logic.

---

### unix.php

Legacy/supporting utility file retained for compatibility purposes.

Not part of the primary CensuScope runtime workflow.

---

## Notes

- Most users only interact directly with `censuscope.py`
- Database preparation scripts are typically run only during setup or database updates
- All reference databases are treated as read-only during normal execution
