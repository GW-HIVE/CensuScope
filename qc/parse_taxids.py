#!/usr/bin/env python3

import argparse
import http.client
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterator, List, Optional, Sequence, Tuple


EUTILS_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# NCBI allows up to 500 IDs per request with an API key
MAX_BATCH_SIZE = 500
DEFAULT_BATCH_SIZE = 200

# Retry config
MAX_RETRIES = 5
BASE_BACKOFF = 2.0      # seconds; doubles each retry
MAX_BACKOFF = 60.0

# HTTP status codes that are transient and worth retrying
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@dataclass
class AccessionRecord:
    accession: str
    tax_id: str = ""


def normalize_accession(accession: str) -> str:
    value = accession.strip().upper()
    if "." in value:
        value = value.split(".", 1)[0]
    return value


def read_accessions(path: str) -> List[str]:
    accessions = []
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            first_column = line.split()[0].strip()
            if line_number == 1 and first_column.lower() in {"accession", "acc", "accession_id"}:
                continue
            accessions.append(first_column)
    return accessions


def chunked(items: Sequence[str], size: int) -> Iterator[List[str]]:
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def parse_record(record: ET.Element) -> AccessionRecord:
    accession = (
        record.findtext("GBSeq_primary-accession")
        or record.findtext("GBSeq_accession-version")
        or record.findtext("GBSeq_locus")
        or ""
    ).strip()
    accession = normalize_accession(accession)
    tax_id = ""

    for feature in record.findall("./GBSeq_feature-table/GBFeature"):
        if (feature.findtext("GBFeature_key") or "").strip() != "source":
            continue
        for qualifier in feature.findall("./GBFeature_quals/GBQualifier"):
            name = (qualifier.findtext("GBQualifier_name") or "").strip()
            value = (qualifier.findtext("GBQualifier_value") or "").strip()
            if name == "db_xref" and value.lower().startswith("taxon:"):
                tax_id = value.split(":", 1)[1].strip()
        break

    return AccessionRecord(accession=accession, tax_id=tax_id)


class NCBIClient:
    def __init__(self, email: Optional[str], api_key: Optional[str], timeout: int) -> None:
        self.email = email
        self.api_key = api_key
        self.timeout = timeout
        # NCBI allows 10 req/s with API key, 3/s without
        self.min_interval = 0.11 if api_key else 0.34
        self.last_request_started = 0.0

    def throttle(self) -> None:
        if self.last_request_started:
            elapsed = time.monotonic() - self.last_request_started
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_request_started = time.monotonic()

    def fetch_batch_xml(self, accessions: Sequence[str]) -> ET.Element:
        """Fetch a batch with exponential backoff retry. Raises on permanent failure."""
        params = {
            "db": "nuccore",
            "id": ",".join(accessions),
            "rettype": "gb",
            "retmode": "xml",
            "tool": "parse_taxids",
        }
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        url = EUTILS_EFETCH_URL + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "parse_taxids/1.0",
                "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
            },
        )

        last_exc: Exception = RuntimeError("No attempts made")

        for attempt in range(MAX_RETRIES):
            self.throttle()
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = response.read()
                return ET.fromstring(payload)

            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code == 400:
                    # Bad request — almost certainly a genuinely invalid accession
                    # in this batch. Don't retry; let the caller split it.
                    raise
                if exc.code in RETRYABLE_STATUS:
                    backoff = min(BASE_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                    sys.stderr.write(
                        f"  HTTP {exc.code} on attempt {attempt + 1}/{MAX_RETRIES},"
                        f" retrying in {backoff:.1f}s\n"
                    )
                    time.sleep(backoff)
                    continue
                # Other 4xx — not worth retrying
                raise

            except (
                urllib.error.URLError,
                TimeoutError,
                http.client.IncompleteRead,
                ET.ParseError,
            ) as exc:
                last_exc = exc
                backoff = min(BASE_BACKOFF * (2 ** attempt), MAX_BACKOFF)
                sys.stderr.write(
                    f"  {type(exc).__name__} on attempt {attempt + 1}/{MAX_RETRIES},"
                    f" retrying in {backoff:.1f}s\n"
                )
                time.sleep(backoff)

        raise last_exc

    def resolve_batch(
        self, accessions: Sequence[str]
    ) -> Tuple[Dict[str, AccessionRecord], List[str]]:
        """
        Resolve a batch of accessions. On HTTP 400 (bad accession somewhere in batch),
        split and recurse — but only then, not for transient errors which are handled
        by fetch_batch_xml's retry loop.
        """
        try:
            root = self.fetch_batch_xml(accessions)

        except urllib.error.HTTPError as exc:
            if exc.code == 400:
                # One or more accessions in this batch are invalid.
                # Binary-split to isolate them.
                if len(accessions) == 1:
                    sys.stderr.write(
                        f"  Permanently unresolvable (HTTP 400): "
                        f"{normalize_accession(accessions[0])}\n"
                    )
                    return {}, [normalize_accession(accessions[0])]

                midpoint = len(accessions) // 2
                left_records, left_failed = self.resolve_batch(accessions[:midpoint])
                right_records, right_failed = self.resolve_batch(accessions[midpoint:])
                left_records.update(right_records)
                return left_records, left_failed + right_failed
            # Non-400 HTTP errors that exhausted all retries
            sys.stderr.write(f"  HTTP {exc.code} after {MAX_RETRIES} retries, marking batch as failed\n")
            return {}, [normalize_accession(a) for a in accessions]

        except Exception as exc:
            sys.stderr.write(
                f"  {type(exc).__name__} after {MAX_RETRIES} retries,"
                f" marking batch as failed\n"
            )
            return {}, [normalize_accession(a) for a in accessions]

        # Parse successful response
        resolved: Dict[str, AccessionRecord] = {}
        for element in root.findall("./GBSeq"):
            record = parse_record(element)
            if record.accession and record.tax_id:
                resolved[record.accession] = record

        # Check for accessions that returned no record at all
        missing = [
            item for item in accessions
            if normalize_accession(item) not in resolved
        ]

        if not missing:
            return resolved, []

        # Some accessions returned no GBSeq element — could be withdrawn/invalid.
        # Try them individually to avoid marking good accessions as failed.
        if len(accessions) > 1 and missing:
            sys.stderr.write(
                f"  {len(missing)} accessions missing from response,"
                f" retrying individually\n"
            )
            for acc in missing:
                sub_records, sub_failed = self.resolve_batch([acc])
                resolved.update(sub_records)
                # sub_failed handled below

            still_missing = [
                item for item in accessions
                if normalize_accession(item) not in resolved
            ]
            return resolved, [normalize_accession(a) for a in still_missing]

        return resolved, [normalize_accession(a) for a in missing]


def get_default_paths() -> Tuple[str, str, str]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "qc_reports")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, "recovered_accession_taxid_" + timestamp + ".tsv")
    unresolved_path = os.path.join(output_dir, "unresolved_accessions_" + timestamp + ".txt")
    checkpoint_path = os.path.join(output_dir, "parse_taxids_checkpoint_" + timestamp + ".txt")
    return output_path, unresolved_path, checkpoint_path


def get_existing_recovered_accessions(path: str) -> set:
    recovered = set()
    if not os.path.exists(path):
        return recovered
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            accession = line.split("\t")[0].strip()
            recovered.add(normalize_accession(accession))
    return recovered


def write_recovered(path: str, records: Dict[str, AccessionRecord]) -> int:
    written = 0
    with open(path, "a", encoding="utf-8", newline="") as handle:
        for accession in sorted(records):
            record = records[accession]
            if record.tax_id:
                handle.write(record.accession + "\t" + record.tax_id + "\n")
                written += 1
        handle.flush()
        os.fsync(handle.fileno())
    return written


def write_unresolved(path: str, accessions: List[str]) -> int:
    if not accessions:
        return 0
    with open(path, "a", encoding="utf-8", newline="") as handle:
        for accession in accessions:
            handle.write(normalize_accession(accession) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return len(accessions)


def write_checkpoint(path: str, processed: int, recovered: int, unresolved: int) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("processed_accessions\t" + str(processed) + "\n")
        handle.write("recovered_taxids\t" + str(recovered) + "\n")
        handle.write("unresolved_accessions\t" + str(unresolved) + "\n")
        handle.write("updated_at\t" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve nucleotide accessions to taxids and output accession_taxid TSV."
    )
    parser.add_argument("input")
    parser.add_argument("--output", default=None)
    parser.add_argument("--unresolved-output", default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"IDs per NCBI request (max {MAX_BATCH_SIZE}, default {DEFAULT_BATCH_SIZE})",
    )
    parser.add_argument("--email", default=os.getenv("NCBI_EMAIL"))
    parser.add_argument("--api-key", default=os.getenv("NCBI_API_KEY"))
    parser.add_argument("--timeout", type=int, default=60)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 1 <= args.batch_size <= MAX_BATCH_SIZE:
        parser.error(f"--batch-size must be between 1 and {MAX_BATCH_SIZE}")

    if not args.api_key:
        sys.stderr.write(
            "Warning: no API key set. Rate limit is 3 req/s."
            " Set NCBI_API_KEY for 10 req/s.\n"
        )

    default_output, default_unresolved, default_checkpoint = get_default_paths()
    output_path = args.output or default_output
    unresolved_path = args.unresolved_output or default_unresolved
    checkpoint_path = args.checkpoint or default_checkpoint

    accessions = read_accessions(args.input)
    if not accessions:
        parser.error("input file does not contain any accessions")

    already_recovered: set = set()
    if args.resume:
        already_recovered = get_existing_recovered_accessions(output_path)

    pending_accessions = [
        a for a in accessions if normalize_accession(a) not in already_recovered
    ]

    client = NCBIClient(email=args.email, api_key=args.api_key, timeout=args.timeout)

    processed = len(accessions) - len(pending_accessions)
    recovered_total = len(already_recovered)
    unresolved_total = 0
    total_pending = len(pending_accessions)

    sys.stderr.write(f"input accessions   : {len(accessions)}\n")
    sys.stderr.write(f"already recovered  : {len(already_recovered)}\n")
    sys.stderr.write(f"pending            : {total_pending}\n")
    sys.stderr.write(f"batch size         : {args.batch_size}\n")
    sys.stderr.write(f"estimated batches  : {(total_pending + args.batch_size - 1) // args.batch_size}\n")
    sys.stderr.write(f"output file        : {output_path}\n")
    sys.stderr.write(f"unresolved file    : {unresolved_path}\n")
    sys.stderr.write(f"checkpoint file    : {checkpoint_path}\n\n")

    try:
        for batch_num, batch in enumerate(chunked(pending_accessions, args.batch_size), start=1):
            records, failed = client.resolve_batch(batch)

            recovered_now = write_recovered(output_path, records)
            unresolved_now = write_unresolved(unresolved_path, failed)

            processed += len(batch)
            recovered_total += recovered_now
            unresolved_total += unresolved_now

            write_checkpoint(checkpoint_path, processed, recovered_total, unresolved_total)

            pct = 100 * processed / len(accessions)
            sys.stderr.write(
                f"batch {batch_num:>6} | processed {processed:>7}/{len(accessions)}"
                f" ({pct:5.1f}%) | recovered {recovered_total:>7}"
                f" | unresolved {unresolved_total:>6}\r"
            )

    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted. Partial results saved.\n")
        sys.stderr.write(f"output file    : {output_path}\n")
        sys.stderr.write(f"unresolved file: {unresolved_path}\n")
        sys.stderr.write(f"checkpoint file: {checkpoint_path}\n")
        return 1

    sys.stderr.write("\n\ndone\n")
    sys.stderr.write(f"processed accessions : {processed}\n")
    sys.stderr.write(f"recovered taxids     : {recovered_total}\n")
    sys.stderr.write(f"unresolved accessions: {unresolved_total}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
