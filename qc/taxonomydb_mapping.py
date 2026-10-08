#!/usr/bin/env python3

"""
This script verifies whether sequence identifiers from an indexed BLAST
nucleotide database, such as slimNT, are present in the CensuScope taxonomy.db
accession_taxid table.
"""

import argparse
import os
import sqlite3
import subprocess
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
    print("BLAST database-taxonomy mapping verification completed.")
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


def extract_blastdb_accessions(blast_db):
    """
    Extract unique accessions and FASTA-style titles from the indexed BLAST database.

    This uses blastdbcmd, so it checks the accessions that BLAST can actually
    return during CensuScope alignment.

    This works best when the BLAST database was built with -parse_seqids.
    """
    cmd = [
        "blastdbcmd",
        "-db", blast_db,
        "-entry", "all",
        "-outfmt", "%a %t",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "blastdbcmd was not found. Please make sure NCBI BLAST+ "
            "is installed and available in your PATH."
        )
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else str(e)

        raise RuntimeError(
            "Failed to extract accessions from BLAST database using "
            f"blastdbcmd. Error: {error_message}"
        )

    accessions = set()
    accession_lookup = {}
    skipped_accessions = 0
    total_entries = 0

    for line in result.stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        total_entries += 1

        parts = line.split(" ", 1)
        original_accession = parts[0]

        if len(parts) > 1:
            title = parts[1]
        else:
            title = ""

        if is_internal_blast_id(original_accession):
            skipped_accessions += 1
            continue

        normalized = normalize_accession(original_accession)

        if is_internal_blast_id(normalized):
            skipped_accessions += 1
            continue

        accessions.add(normalized)

        if title:
            accession_lookup[normalized] = f">{original_accession} {title}"
        else:
            accession_lookup[normalized] = f">{original_accession}"

    return (
        sorted(accessions),
        accession_lookup,
        total_entries,
        skipped_accessions,
    )


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


def format_missing_accession_lines(missing_accessions, accession_lookup):
    """
    Format missing accession output with normalized accession and full
    FASTA-style BLAST database header.

    Output format:
    accession<TAB>blastdb_header
    """
    output_lines = [
        "accession\tblastdb_header"
    ]

    for accession in missing_accessions:
        blastdb_header = accession_lookup.get(accession, "")
        output_lines.append(f"{accession}\t{blastdb_header}")

    return output_lines


def verify_mapping(
    blast_db,
    taxonomy_db,
    report_file,
    missing_output,
    max_show,
    batch_size,
):
    report_lines = []
    warnings = []

    log(
        "===== BLAST Database-Taxonomy Mapping Verification Report =====",
        report_lines,
    )

    log(f"BLAST database: {blast_db}", report_lines)
    log(f"taxonomy.db: {taxonomy_db}", report_lines)

    try:
        log(
            "\nExtracting accessions and titles from BLAST database "
            "using blastdbcmd...",
            report_lines,
        )

        (
            blastdb_accessions,
            accession_lookup,
            total_entries,
            skipped_accessions,
        ) = extract_blastdb_accessions(blast_db)

        total_blastdb = len(blastdb_accessions)

        log(
            f"Total BLAST database entries returned: {total_entries}",
            report_lines,
        )

        log(
            f"Unique BLAST database accessions extracted: "
            f"{total_blastdb}",
            report_lines,
        )

        log(
            f"Accessions skipped during extraction: "
            f"{skipped_accessions}",
            report_lines,
        )

        if total_blastdb == 0:
            raise RuntimeError(
                "No accessions were extracted from the BLAST database. "
                "This usually means the database was built without "
                "-parse_seqids."
            )

        if not os.path.isfile(taxonomy_db):
            raise FileNotFoundError(
                f"taxonomy.db not found: {taxonomy_db}"
            )

        log(
            "\nChecking extracted accessions against taxonomy.db in batches...",
            report_lines,
        )

        log(f"Batch size: {batch_size}", report_lines)

        conn = sqlite3.connect(taxonomy_db)
        cursor = conn.cursor()

        missing_accessions = []

        for batch_number, batch in enumerate(
            chunk_list(blastdb_accessions, batch_size),
            start=1,
        ):
            found = lookup_accessions_in_taxonomy_db(cursor, batch)

            missing_in_batch = sorted(set(batch) - found)

            if missing_in_batch:
                missing_accessions.extend(missing_in_batch)

            if batch_number % 100 == 0:
                log(
                    f"Processed "
                    f"{min(batch_number * batch_size, total_blastdb)} "
                    f"of {total_blastdb} extracted accessions...",
                    report_lines,
                )

        conn.close()

    except Exception as e:
        error_message = str(e)

        if "-parse_seqids" in error_message:
            log(
                "\nWARNING: No usable accession IDs were extracted from "
                "the BLAST database.",
                report_lines,
            )

            log(
                "This BLAST database was likely built without "
                "-parse_seqids.",
                report_lines,
            )

            log(
                "Rebuild the database using:",
                report_lines,
            )

            log(
                "makeblastdb -in INPUT.fa -dbtype nucl "
                "-parse_seqids -out DATABASE_NAME",
                report_lines,
            )

            log("\n===== Summary =====", report_lines)

            log(
                "WARNING: BLAST database-taxonomy mapping verification "
                "completed with missing accessions.",
                report_lines,
            )

            write_file(report_file, report_lines)

            print_final_message(
                "WARNING: BLAST database-taxonomy mapping verification "
                "completed with missing accessions.",
                report_file,
            )

            return 0

        log(f"\nFAIL: {e}", report_lines)

        log("\n===== Summary =====", report_lines)

        log(
            "FAIL: BLAST database-taxonomy mapping verification failed.",
            report_lines,
        )

        write_file(report_file, report_lines)

        print_final_message(
            "FAIL: BLAST database-taxonomy mapping verification failed.",
            report_file,
        )

        return 1

    missing_accessions = remove_internal_blast_ids(
        missing_accessions
    )

    total_missing = len(missing_accessions)
    total_mapped = total_blastdb - total_missing

    if total_blastdb == 0:
        missing_percent = 0
    else:
        missing_percent = total_missing / total_blastdb * 100

    log("\n===== Mapping Summary =====", report_lines)

    log(
        f"Total unique BLAST database accessions checked: "
        f"{total_blastdb}",
        report_lines,
    )

    log(
        f"Mapped in taxonomy.db: {total_mapped}",
        report_lines,
    )

    log(
        f"Missing from taxonomy.db: {total_missing}",
        report_lines,
    )

    log(
        f"Missing percentage: {missing_percent:.2f}%",
        report_lines,
    )

    missing_file_created = None

    if total_missing > 0:
        warnings.append(
            f"{total_missing} BLAST database accessions are "
            f"missing from taxonomy.db"
        )

        log(
            "\nWARNING: Some BLAST database accessions are "
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

        missing_output_lines = format_missing_accession_lines(
            missing_accessions,
            accession_lookup,
        )

        write_file(missing_output, missing_output_lines)

        missing_file_created = missing_output

        log(
            f"\nFull missing accession list written to: "
            f"{missing_output}",
            report_lines,
        )

    else:
        log(
            "\nPASS: all BLAST database accessions are found "
            "in taxonomy.db",
            report_lines,
        )

        if os.path.exists(missing_output):
            os.remove(missing_output)

    log("\n===== Summary =====", report_lines)

    if warnings:
        log("Warnings:", report_lines)

        for warning in warnings:
            log(f"- {warning}", report_lines)

        log(
            "\nWARNING: BLAST database-taxonomy mapping verification "
            "completed with missing accessions.",
            report_lines,
        )

        terminal_status = (
            "WARNING: BLAST database-taxonomy mapping verification "
            "completed with missing accessions."
        )

    else:
        log(
            "\nPASS: all BLAST database accessions are found "
            "in taxonomy.db.",
            report_lines,
        )

        terminal_status = (
            "PASS: all BLAST database accessions are found "
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
            "Verify mapping coverage between BLAST database accessions "
            "and taxonomy.db."
        )
    )

    parser.add_argument(
        "--blast-db",
        required=True,
        help=(
            "BLAST database prefix, for example "
            "database/slimNT or database/refseq_database_FinalTest"
        ),
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
        default=20,
        help=(
            "Maximum number of missing accessions shown "
            "in the report. Default: 20"
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
        args.blast_db,
        args.taxonomy_db,
        args.report,
        args.missing_output,
        args.max_show,
        args.batch_size,
    )

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
