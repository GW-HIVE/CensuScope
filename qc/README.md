# Taxonomy Database QC Verification
This directory contains optional QC verification scripts for validating the taxonomy database structure and NCBI BLAST database-to-taxonomy mapping coverage in CensuScope.

## When to Run
These QC verification scripts are OPTIONAL and are not required for every run. We recommend running them in the following situations:
1. During the initial CensuScope setup
2. After rebuilding or updating taxonomy.db
3. After updating or replacing your NCBI BLAST database
4. When troubleshooting unexpected classification results

## Scripts

### 1. taxonomydb_verification.py — Database Structure Verification

Verifies the structure and integrity of `taxonomy.db`. Recommended before running FASTA-to-taxonomy mapping verification.

**What it checks:**
- `taxonomy.db` file exists and is non-empty
- Database is readable as a valid SQLite file
- All required tables are present (`nodes`, `names`, `accession_taxid`)
- Required columns exist in each table
- Row counts to ensure required tables are non-empty
- `nodes` and `names` JOIN compatibility
- Nodes missing scientific name entries

**Output:**
- Report written to: `qc/qc_reports/taxonomy_db_verification_report.txt`

**Command:**

Run the following command from the `CensuScope` root directory:
```bash
python3 verify_taxonomy_db.py \
  --taxonomy-db path/to/taxonomy.db
```
