# Troubleshooting

## Taxonomy database schema mismatch

**Symptom:** CensuScope fails with a column not found or missing table error.

**Cause:** The `taxonomy.db` was built from a raw NCBI dump without renaming columns to match the CensuScope schema. NCBI's `names.dmp` uses `tax_id` and `name_txt`; CensuScope expects `taxid` and `name`.

**Fix:**
```bash
sqlite3 taxonomy.db "ALTER TABLE names RENAME COLUMN name_txt TO name;"
sqlite3 taxonomy.db "ALTER TABLE nodes RENAME COLUMN tax_id TO taxid;"
```

See [docs/taxonomy.md](taxonomy.md) for the full expected schema.

---

## Missing BLAST database

**Symptom:** CensuScope exits with a BLAST database not found error.

**Cause:** The BLAST database path is incorrect or the index files (`.nin`, `.nsq`, `.nhr`) are missing.

**Fix:**
1. Verify the database path is correct and accessible.
2. Confirm that `makeblastdb` was run against your FASTA file:
   ```bash
   makeblastdb -in reference.fasta -dbtype nucl -parse_seqids -out blast_db/reference
   ```
3. In Docker, ensure the database directory is mounted correctly:
   ```bash
   -v /path/to/blast_db:/app/blastdb
   ```

---

## Docker volume issues (macOS)

**Symptom:** `Mounts denied` error when running the container on macOS.

**Fix:**
1. Open Docker Desktop.
2. Go to **Settings > Resources > File Sharing**.
3. Add the parent directory of your data (e.g., `/Users/yourname/data`).
4. Click **Apply & Restart**.

---

## BLAST not found (CLI)

**Symptom:**
```
blastn: command not found
```

**Fix:** Install BLAST+ and ensure it is on your `PATH`.

```bash
# Linux
sudo apt-get install -y ncbi-blast+

# macOS
brew install blast
```

Verify:
```bash
blastn -version
```

---

## Slow performance

- Reduce `--sample-size` or `--iterations` for faster runs during development.
- Large BLAST databases will increase per-iteration runtime; this is expected.
- SQLite taxonomy lookups are generally fast and are not usually the bottleneck.
