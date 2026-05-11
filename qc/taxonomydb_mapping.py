#!/usr/bin/env python3

"""
This script verifies whether title-derived sequence identifiers from a FASTA
database file, such as slimNT.fa, are present in the CensuScope taxonomy.db
accession_taxid table.

Verification checks include:
- FASTA header parsing
- title-derived accession extraction
- batch lookup of extracted accessions in taxonomy.db
- mapping coverage between FASTA-derived accessions and taxonomy.db

A detailed mapping verification report is written to: qc/qc_reports/taxonomy_mapping_report_TIMESTAMP.txt
If missing accessions are found, they are written to: qc/qc_reports/missing_accessions_TIMESTAMP.txt
If no missing accessions are found, no missing_accessions file is created.
"""

import argparse
import os
import sqlite3
from datetime import datetime


TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

DEFAULT_REPORT = (
    f"qc/qc_reports/taxonomy_mapping_report_{TIMESTAMP}.txt"
)

DEFAULT_MISSING_OUTPUT = (
    f"qc/qc_reports/missing_accessions_{TIMESTAMP}.txt"
)


def log(message, report_lines):
    report_lines.append(message)


def write_file(output_file, lines):
    output_dir = os.path.dirname(output_file)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w") as f:
        f.write("\n".join(lines) + "\n")


def print_final_message(status_message, report_file, missing_file=None):
    print(status_message)
    print("FASTA-taxonomy mapping verification completed.")
    print(f"See report: {report_file}")

    if missing_file:
        print(f"Missing accessions written to: {missing_file}")


def normalize_accession(accession):
    """
    Remove version suffix from accession.
    Example: ABC123.1 -> ABC123
    """
    return accession.split(".", 1)[0]


def is_internal_blast_id(accession):
    """
    Detect BLAST internal identifiers that should not be treated as real accessions.
    """
    if not accession:
        return True

    if "BL_ORD_ID" in accession:
        return True

    if accession.startswith("gnl|"):
        return True

    return False


def extract_accession_from_header(header):
    """
    Extract accession from the first token of a FASTA header.

    Example:
    >AAILSW010000053.1 Salmonella enterica ...

    Extracted:
    AAILSW010000053
    """
    header = header.strip()

    if header.startswith(">"):
        header = header[1:].strip()

    if not header:
        return None

    first_token = header.split()[0]

    if is_internal_blast_id(first_token):
        return None

    return normalize_accession(first_token)


def extract_fasta_accessions(fasta_file):
    """
    Extract unique title-derived accessions from FASTA headers.
    """
    if not os.path.isfile(fasta_file):
        raise FileNotFoundError(f"FASTA file not found: {fasta_file}")

    accessions = set()
    skipped_headers = 0
    total_headers = 0

    with open(fasta_file, "r") as f:
        for line in f:
            if line.startswith(">"):
                total_headers += 1

                accession = extract_accession_from_header(line)

                if accession:
                    accessions.add(accession)
                else:
                    skipped_headers += 1

    return sorted(accessions), total_headers, skipped_headers


def chunk_list(items, chunk_size):
    """
    Yield chunks from a list.
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def lookup_accessions_in_taxonomy_db(cursor, accessions):
    """
    Look up one batch of accessions in taxonomy.db.
    """
    placeholders = ",".join(["?"] * len(accessions))

    query = f"""
    SELECT accession
    FROM accession_taxid
    WHERE accession IN ({placeholders})
    """

    cursor.execute(query, accessions)

    found = set()

    for row in cursor.fetchall():
        accession = row[0]

        if accession:
            normalized = normalize_accession(accession)

            if not is_internal_blast_id(normalized):
                found.add(normalized)

    return found


def remove_internal_blast_ids(accessions):
    """
    Remove BLAST internal IDs before reporting.
    """
    return [
        accession for accession in accessions
        if not is_internal_blast_id(accession)
    ]


def verify_mapping(
    fasta_file,
    taxonomy_db,
    report_file,
    missing_output,
    max_show,
    batch_size,
):
    report_lines = []
    warnings = []

    log("===== FASTA-Taxonomy Mapping Verification Report =====", report_lines)
    log(f"FASTA file: {fasta_file}", report_lines)
    log(f"taxonomy.db: {taxonomy_db}", report_lines)

    try:
        log(
            "\nExtracting title-derived accessions from FASTA headers...",
            report_lines
        )

        fasta_accessions, total_headers, skipped_headers = (
            extract_fasta_accessions(fasta_file)
        )

        total_fasta = len(fasta_accessions)

        log(f"Total FASTA headers found: {total_headers}", report_lines)

        log(
            f"Unique title-derived accessions extracted: {total_fasta}",
            report_lines
        )

        log(
            f"Headers skipped during accession extraction: {skipped_headers}",
            report_lines
        )

        if total_fasta == 0:
            raise RuntimeError(
                "No accessions were extracted from the FASTA file."
            )

        if not os.path.isfile(taxonomy_db):
            raise FileNotFoundError(
                f"taxonomy.db not found: {taxonomy_db}"
            )

        log(
            "\nChecking extracted accessions against taxonomy.db in batches...",
            report_lines
        )

        log(f"Batch size: {batch_size}", report_lines)

        conn = sqlite3.connect(taxonomy_db)
        cursor = conn.cursor()

        missing_accessions = []

        for batch_number, batch in enumerate(
            chunk_list(fasta_accessions, batch_size),
            start=1,
        ):
            found = lookup_accessions_in_taxonomy_db(cursor, batch)

            missing_in_batch = sorted(set(batch) - found)

            if missing_in_batch:
                missing_accessions.extend(missing_in_batch)

            if batch_number % 100 == 0:
                log(
                    f"Processed "
                    f"{min(batch_number * batch_size, total_fasta)} "
                    f"of {total_fasta} extracted accessions...",
                    report_lines,
                )

        conn.close()

    except Exception as e:
        log(f"\nFAIL: {e}", report_lines)

        log("\n===== Summary =====", report_lines)

        log(
            "FAIL: FASTA-taxonomy mapping verification failed.",
            report_lines
        )

        write_file(report_file, report_lines)

        print_final_message(
            "FAIL: FASTA-taxonomy mapping verification failed.",
            report_file,
        )

        return 1

    # Final safety filter
    missing_accessions = remove_internal_blast_ids(
        missing_accessions
    )

    total_missing = len(missing_accessions)
    total_mapped = total_fasta - total_missing

    if total_fasta == 0:
        missing_percent = 0
    else:
        missing_percent = total_missing / total_fasta * 100

    log("\n===== Mapping Summary =====", report_lines)

    log(
        f"Total unique title-derived accessions checked: {total_fasta}",
        report_lines
    )

    log(
        f"Mapped in taxonomy.db: {total_mapped}",
        report_lines
    )

    log(
        f"Missing from taxonomy.db: {total_missing}",
        report_lines
    )

    log(
        f"Missing percentage: {missing_percent:.2f}%",
        report_lines
    )

    missing_file_created = None

    if total_missing > 0:
        warnings.append(
            f"{total_missing} title-derived accessions are "
            f"missing from taxonomy.db"
        )

        log(
            "\nWARNING: Some title-derived accessions are "
            "missing from taxonomy.db.",
            report_lines,
        )

        log(
            f"Showing first {min(max_show, total_missing)} "
            f"missing accessions:",
            report_lines,
        )

        for accession in missing_accessions[:max_show]:
            log(accession, report_lines)

        write_file(missing_output, missing_accessions)

        missing_file_created = missing_output

        log(
            f"\nFull missing accession list written to: "
            f"{missing_output}",
            report_lines
        )

    else:
        log(
            "\nPASS: all title-derived accessions are found "
            "in taxonomy.db",
            report_lines
        )

        if os.path.exists(missing_output):
            os.remove(missing_output)

    log("\n===== Summary =====", report_lines)

    if warnings:
        log("Warnings:", report_lines)

        for warning in warnings:
            log(f"- {warning}", report_lines)

        log(
            "\nWARNING: FASTA-taxonomy mapping verification "
            "completed with missing accessions.",
            report_lines,
        )

        terminal_status = (
            "WARNING: FASTA-taxonomy mapping verification "
            "completed with missing accessions."
        )

    else:
        log(
            "\nPASS: all title-derived accessions are found "
            "in taxonomy.db.",
            report_lines
        )

        terminal_status = (
            "PASS: all title-derived accessions are found "
            "in taxonomy.db."
        )

    write_file(report_file, report_lines)

    print_final_message(
        terminal_status,
        report_file,
        missing_file_created,
    )

    return 0


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Verify mapping coverage between FASTA "
            "title-derived accessions and taxonomy.db."
        )
    )

    parser.add_argument(
        "--fasta",
        required=True,
        help="Input FASTA file, for example database/slimNT.fa",
    )

    parser.add_argument(
        "--taxonomy-db",
        required=True,
        help="Path to taxonomy.db",
    )

    parser.add_argument(
        "--report",
        default=DEFAULT_REPORT,
        help="Output mapping verification report file",
    )

    parser.add_argument(
        "--missing-output",
        default=DEFAULT_MISSING_OUTPUT,
        help=(
            "Output file for missing accessions. "
            "Only created if missing accessions exist."
        ),
    )

    parser.add_argument(
        "--max-show",
        type=int,
        default=50,
        help=(
            "Maximum number of missing accessions shown "
            "in the report. Default: 50"
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help=(
            "Number of extracted accessions checked per "
            "SQLite query. Default: 1000"
        ),
    )

    args = parser.parse_args()

    exit_code = verify_mapping(
        args.fasta,
        args.taxonomy_db,
        args.report,
        args.missing_output,
        args.max_show,
        args.batch_size,
    )

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
