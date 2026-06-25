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

### 2. taxonomydb_mapping.py — BLAST Database Mapping Verification

Verifies NCBI BLAST database-to-taxonomy mapping coverage by comparing indexed BLAST database accessions against the `accession_taxid` table in `taxonomy.db`.

Recommended after confirming that `taxonomy.db` passes database structure verification.

**What it checks:**

- BLAST database exists and is readable

- Accessions can be extracted from the indexed BLAST database using `blastdbcmd`

- Accessions are normalized before lookup

- Extracted accessions are checked against `accession_taxid`

- BLAST internal identifiers such as `BL_ORD_ID` and `gnl|` are excluded

- Missing accessions are reported with their original BLAST database headers

- Detects databases built without `-parse_seqids`

**Requirements:**

- NCBI BLAST+ must be installed and available in `PATH`

- The BLAST database should be built using `-parse_seqids`

Example:

```bash
makeblastdb -in database/slimNT.fa -dbtype nucl -parse_seqids -out database/slimNT
```

**Output:**

- Mapping summary report written to:

  `qc/qc_reports/taxonomy_mapping_report_TIMESTAMP.txt`

- Missing accession report written to:

  `qc/qc_reports/missing_accessions_TIMESTAMP.txt`

**Example PASS terminal output:**

```text
PASS: all BLAST database accessions are found in taxonomy.db.

BLAST database-taxonomy mapping verification completed.
See report: qc/qc_reports/taxonomy_mapping_report_TIMESTAMP.txt
```

**Example terminal output(missing accessions detected):**
```text

WARNING: BLAST database-taxonomy mapping verification completed with missing accessions.
BLAST database-taxonomy mapping verification completed.
See report: qc/qc_reports/taxonomy_mapping_report_TIMESTAMP.txt
Missing accessions written to:
qc/qc_reports/missing_accessions_TIMESTAMP.txt

```

**Command:**

Run the following commands from the `CensuScope` root directory:

```bash

python qc/taxonomydb_mapping.py \
  --blast-db path/to/blast_database_prefix \
  --taxonomy-db path/to/taxonomy.db

```

Specific example:

```bash

python qc/taxonomydb_mapping.py \
  --blast-db database/slimNT \
  --taxonomy-db database/taxonomy.db

```
---
## 3. parse_taxids.py — Accession-to-TaxID Recovery

Recovers accession-to-taxid mappings that are missing from `taxonomy.db` by querying NCBI Entrez E-utilities.

Recommended when `taxonomydb_mapping.py` reports accessions that are missing from `taxonomy.db`.

**NCBI API Key (Recommended):**

Using an API key increases the allowable NCBI request rate.

1. Sign in to My NCBI.
2. Open **Account Settings**.
3. Navigate to **API Key Management**.
4. Create or view your API key.

Export the key before running the script:

```bash
export NCBI_API_KEY="YOUR_API_KEY"
```

Verify:

```bash
echo $NCBI_API_KEY
```
More information about API keys can be found [here](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/api/api-keys/).

**Run:**

Optional Parameters:

- `--batch-size`: Number of accessions queried per NCBI request (maximum: 500; default: 200).
- `--timeout`: Maximum time to wait for an NCBI response before the request is considered failed (default: 60).
- `--resume`: Resume a previously interrupted run using the existing recovered accession TSV file specified by --output.

```bash
python parse_taxids.py \qc_reports/missing_accessions_TIMESTAMP.txt
```

**Checkpoint and Resume**

For large accession sets, the script automatically generates a checkpoint file:

```text
qc_reports/parse_taxids_checkpoint_TIMESTAMP.txt
```

The checkpoint file records run progress, including the number of processed, recovered, and unresolved accessions.

Recovered mappings are written incrementally to:

```text
qc_reports/recovered_accession_taxid_TIMESTAMP.tsv
```

If a run is interrupted, resume by using `--resume` with the same output file from the interrupted run:

```bash
python parse_taxids.py \
    qc_reports/missing_accessions_TIMESTAMP.txt \
    --resume \
    --output qc_reports/recovered_accession_taxid_TIMESTAMP.tsv
```

This allows the script to skip accessions that were already recovered and continue processing the remaining accessions.

**This generates:**

```text
qc_reports/recovered_accession_taxid_TIMESTAMP.tsv
qc_reports/unresolved_accessions_TIMESTAMP.txt
qc_reports/parse_taxids_checkpoint_TIMESTAMP.txt
```

**To import recovered mappings into taxonomy.db:**

Run the following commands from the `CensuScope` root directory

Run the following command from the **CensuScope** root directory:

```bash

sqlite3 database/taxonomy.db

```

Create a temporary table:

```
CREATE TEMP TABLE recovered_accession_taxid (accession TEXT, taxid INTEGER);
```

Set the import mode:

```
.mode tabs
```

Import the recovered mappings:

```
.import qc/qc_reports/recovered_accession_taxid_TIMESTAMP.tsv recovered_accession_taxid
```
Insert the recovered mappings into `accession_taxid`:

```
INSERT OR IGNORE INTO accession_taxid(accession, taxid)
SELECT accession, taxid
FROM recovered_accession_taxid;
```
Exit SQLite:

```
.quit
```

After importing the recovered mappings, rerun `taxonomydb_mapping.py` to verify that the missing accession count has been reduced or eliminated.
