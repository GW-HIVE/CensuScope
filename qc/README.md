# Taxonomy Database QC Verification

This directory contains optional QC verification scripts for validating taxonomy database structure and NCBI BLAST database-to-taxonomy mapping coverage in CensuScope.

## When to Run

These QC verification scripts are OPTIONAL and are not required for every run. We recommend running them in the following situations:

1. During the initial CensuScope setup
2. After rebuilding or updating `taxonomy.db`
3. After updating or replacing your NCBI BLAST database
4. When troubleshooting unexpected classification results

---

## Scripts

### 1. taxonomydb_verification.py — Database Structure Verification

Verifies the structure and integrity of `taxonomy.db`. Recommended before running BLAST database-to-taxonomy mapping verification.

**What it checks:**
- `taxonomy.db` file exists and is non-empty
- Database is readable as a valid SQLite file
- All required tables are present (`nodes`, `names`, `accession_taxid`)
- Required columns exist in each table
- Row counts to ensure required tables are non-empty
- `nodes` and `names` JOIN compatibility
- Checks for nodes missing scientific name entries

**Output:**
- Report written to: `qc/qc_reports/taxonomy_db_verification_report.txt`

**Example terminal output:**

```text
PASS: taxonomy.db is valid for CensuScope.

Taxonomy database verification completed.
See report: qc/qc_reports/taxonomy_db_verification_report.txt
```

**Command:**

Run the following command from the `CensuScope` root directory:

```bash
python qc/taxonomydb_verification.py \
  --taxonomy-db path/to/taxonomy.db
```

---

### 2. taxonomydb_mapping.py — Database Mapping Verification

Verifies NCBI BLAST database-to-taxonomy mapping coverage by comparing FASTA-derived accessions against the `accession_taxid` table in `taxonomy.db`.

Recommended after confirming that `taxonomy.db` passes database structure verification.

**What it checks:**
- FASTA database file exists and is readable
- Accessions can be extracted from FASTA headers
- Accession versions are normalized before lookup
- Extracted accessions are checked against `accession_taxid`
- BLAST internal identifiers such as `BL_ORD_ID` and `gnl|` are excluded
- Missing accessions are reported with their original FASTA headers

**Output:**
- Mapping summary report written to: `qc/qc_reports/taxonomy_mapping_report_TIMESTAMP.txt`
- Missing accession report written to: `qc/qc_reports/missing_accessions_TIMESTAMP.txt`

**Example terminal output:**

```text
WARNING: FASTA-taxonomy mapping verification completed with missing accessions.

FASTA-taxonomy mapping verification completed.
See report: qc/qc_reports/taxonomy_mapping_report_TIMESTAMP.txt

Missing accessions written to:
qc/qc_reports/missing_accessions_TIMESTAMP.txt
```

**Command:**

Run the following command from the `CensuScope` root directory:

```bash
python qc/taxonomydb_mapping.py \
  --fasta path/to/database.fasta \
  --taxonomy-db path/to/taxonomy.db
```

For example:

```bash
python qc/taxonomydb_mapping.py \
  --fasta database/slimNT.fa \
  --taxonomy-db database/taxonomy.db
```
