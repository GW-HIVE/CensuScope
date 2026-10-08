# Output Files

CensuScope writes all output to a timestamped directory within the configured output path. Output is written per-run; no state is shared between runs.

## Files Produced

| File | Description | Type |
|------|-------------|------|
| `taxonomy_table.tsv` | Aggregated taxonomic counts | Stable output |
| `tax_tree.json` | Hierarchical taxonomy tree | Stable output |
| `censuscope.log` | Execution log | Stable output |
| Intermediate BLAST files | Per-iteration BLAST output | Intermediate |

Stable outputs are suitable for downstream analysis. Intermediate files reflect per-iteration sampling results and may vary between runs.

## Output Location

Output location is controlled via CLI options. In Docker deployments, outputs are written to `/app/temp_dirs` inside the container and mapped to the host via a volume mount.

## Reproducibility

Because CensuScope uses stochastic read sampling, output files may differ between runs with identical inputs. This is expected behavior. Increasing `--iterations` and `--sample-size` reduces variability but does not eliminate it.

---

> This document is a stub. Content will be expanded as output formats are finalized.
