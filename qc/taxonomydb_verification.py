#!/usr/bin/env python3

"""
This script verifies the structure and basic integrity of the taxonomy.db database used by CensuScope.

Verification checks include:
- taxonomy.db file existence
- SQLite readability
- required table existence
- required column existence
- non-empty required tables
- nodes/names JOIN compatibility
- missing scientific name detection

A detailed verification report is written to: qc/qc_reports/taxonomy_db_verification_report.txt
"""

import argparse
import os
import sqlite3


REQUIRED_TABLES = ["nodes", "names", "accession_taxid"]
OPTIONAL_TABLES = ["hosts"]

EXPECTED_COLUMNS = {
    "nodes": ["taxid", "parent_taxid", "rank"],
    "names": ["taxid", "name"],
    "accession_taxid": ["accession", "taxid"],
}


def log(message, report_lines):
    report_lines.append(message)


def write_report(output_file, report_lines):
    output_dir = os.path.dirname(output_file)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w") as f:
        f.write("\n".join(report_lines) + "\n")


def get_tables(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}


def get_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def get_count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]


def print_final_message(status_message, output_file):
    print(status_message)
    print("Taxonomy database verification completed.")
    print(f"See report: {output_file}")


def verify_taxonomy_db(taxonomy_db, output_file):
    report_lines = []
    problems = []
    warnings = []

    log("===== Taxonomy DB Verification Report =====", report_lines)
    log(f"Database: {taxonomy_db}", report_lines)

    if not os.path.isfile(taxonomy_db):
        log(f"FAIL: taxonomy.db not found: {taxonomy_db}", report_lines)
        write_report(output_file, report_lines)
        print_final_message("FAIL: taxonomy.db verification failed.", output_file)
        return 1

    if os.path.getsize(taxonomy_db) == 0:
        log(f"FAIL: taxonomy.db is empty: {taxonomy_db}", report_lines)
        write_report(output_file, report_lines)
        print_final_message("FAIL: taxonomy.db verification failed.", output_file)
        return 1

    try:
        conn = sqlite3.connect(taxonomy_db)
        cursor = conn.cursor()
        log("PASS: database can be opened by SQLite", report_lines)
    except sqlite3.Error as e:
        log(f"FAIL: cannot open taxonomy.db as SQLite database: {e}", report_lines)
        write_report(output_file, report_lines)
        print_final_message("FAIL: taxonomy.db verification failed.", output_file)
        return 1

    tables = get_tables(cursor)

    log("\nDetected tables:", report_lines)
    for table in sorted(tables):
        log(f"- {table}", report_lines)

    for table in REQUIRED_TABLES:
        if table not in tables:
            problems.append(f"Missing required table: {table}")
        else:
            log(f"\nPASS: required table exists: {table}", report_lines)

    for table in OPTIONAL_TABLES:
        if table not in tables:
            warnings.append(f"Optional/legacy table not found: {table}")
        else:
            log(f"PASS: optional table exists: {table}", report_lines)

    if problems:
        conn.close()

        log("\n===== Summary =====", report_lines)
        log("FAIL: missing required tables.", report_lines)

        for problem in problems:
            log(f"- {problem}", report_lines)

        write_report(output_file, report_lines)
        print_final_message("FAIL: taxonomy.db verification failed.", output_file)
        return 1

    log("\n===== Column Checks =====", report_lines)

    for table, expected_columns in EXPECTED_COLUMNS.items():
        columns = get_columns(cursor, table)

        log(f"\n{table} columns: {', '.join(sorted(columns))}", report_lines)

        missing_columns = [
            col for col in expected_columns
            if col not in columns
        ]

        if missing_columns:
            problems.append(
                f"Table '{table}' missing columns: {', '.join(missing_columns)}"
            )
            log(
                f"FAIL: {table} missing columns: {', '.join(missing_columns)}",
                report_lines
            )
        else:
            log(f"PASS: {table} contains required columns", report_lines)

    log("\n===== Row Count Checks =====", report_lines)

    for table in REQUIRED_TABLES:
        count = get_count(cursor, table)
        log(f"{table}: {count} rows", report_lines)

        if count == 0:
            problems.append(f"Table '{table}' is empty")

    log("\n===== CensuScope Compatibility Join Check =====", report_lines)

    try:
        query = """
        SELECT n.taxid, na.name, n.rank, n.parent_taxid
        FROM nodes n
        JOIN names na ON n.taxid = na.taxid
        LIMIT 10
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            log("PASS: nodes/names join works", report_lines)
        else:
            warnings.append("nodes/names join succeeded but returned no rows")
            log("WARNING: nodes/names join returned no rows", report_lines)

    except sqlite3.Error as e:
        problems.append(f"CensuScope compatibility join failed: {e}")
        log(f"FAIL: CensuScope compatibility join failed: {e}", report_lines)

    log("\n===== Missing Scientific Name Check =====", report_lines)

    try:
        query = """
        SELECT COUNT(*)
        FROM nodes n
        LEFT JOIN names na ON n.taxid = na.taxid
        WHERE na.name IS NULL
        """
        cursor.execute(query)
        missing_names = cursor.fetchone()[0]

        log(f"Nodes missing names: {missing_names}", report_lines)

        if missing_names > 0:
            warnings.append(f"{missing_names} nodes do not have names")

    except sqlite3.Error as e:
        warnings.append(f"Could not run missing-name check: {e}")
        log(f"WARNING: could not run missing-name check: {e}", report_lines)

    conn.close()

    log("\n===== Summary =====", report_lines)

    if warnings:
        log("Warnings:", report_lines)
        for warning in warnings:
            log(f"- {warning}", report_lines)

    if problems:
        log("\nFAIL: taxonomy.db verification failed.", report_lines)

        for problem in problems:
            log(f"- {problem}", report_lines)

        exit_code = 1
        terminal_status = "FAIL: taxonomy.db verification failed."
    else:
        log("\nPASS: taxonomy.db is valid for CensuScope.", report_lines)

        exit_code = 0
        terminal_status = "PASS: taxonomy.db is valid for CensuScope."

    write_report(output_file, report_lines)
    print_final_message(terminal_status, output_file)

    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Verify taxonomy.db schema and basic CensuScope compatibility."
    )

    parser.add_argument(
        "--taxonomy-db",
        required=True,
        help="Path to taxonomy.db"
    )

    parser.add_argument(
        "--output",
        default="qc/qc_reports/taxonomy_db_verification_report.txt",
        help="Output report file"
    )

    args = parser.parse_args()

    exit_code = verify_taxonomy_db(
        args.taxonomy_db,
        args.output
    )

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()