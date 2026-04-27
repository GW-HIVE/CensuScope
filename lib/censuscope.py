#!/usr/bin/env python3
"""
"""

import argparse
import csv
import json
import os
import logging
import random
import subprocess
import sqlite3
import sys
import time 
from collections import defaultdict
from datetime import datetime
from threading import Thread, Lock
import re

write_lock = Lock()

def normalize_accession(acc: str) -> str:
	if not acc:
		return acc
	return acc.split(".", 1)[0]

__version__ = "0.1"
__status__ = "BETA"


class GlobalState:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.start_time = datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z')
        self.temp_path = f"{self.base_dir}/temp_dirs/{self.start_time}"
        # self.temp_path = f"{self.base_dir}/temp_dirs"   #For debugging
        self.temp_dirs = {
            "random_samples": f"{self.temp_path}/random_samples",
            "results": f"{self.temp_path}/results",
            "blastn": f"{self.temp_path}/blastn",
            "inputs": f"{self.temp_path}/inputs",
        }
        self.iteration_count = 0
        self.tax_tree = {}

        os.makedirs(self.temp_path, exist_ok=True)
        for dir_path in self.temp_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

global_state = GlobalState()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

log_file_path = os.path.join(global_state.temp_dirs["results"], "censuscope.log")

# Full format for the log file
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

# Cleaner format for terminal output
stream_formatter = logging.Formatter(
    '%(asctime)s - %(message)s'
)

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Stream handler: only show important things in terminal
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
stream_handler.setFormatter(stream_formatter)

if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.info("Global State values set: "+
    f"\n\tStart Time: {global_state.start_time},\n\tBase directory: {global_state.base_dir}, "+
    f"\n\tTemp path: {global_state.temp_path}"
)

def usr_args():
    """User supplied arguments for functions
    """

    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(
        prog='censuscope',
        usage='%(prog)s [options]')

    # version
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ' + __version__)
    
    parser.add_argument(
        "-i", '--iterations',
        required=True,
        help="The number of sample iterations to perform"
    )

    parser.add_argument(
        "-s", '--sample-size',
        required=True,
        help="The number of reads to sample for each iteration"
    )

    parser.add_argument(
        "-t", '--tax-depth',
        choices=["kingdom", "phylum", "class", "order", "family", "genus", "species"],
        required=True,
        help="The taxonomy depth to report in the final results"
    )

    parser.add_argument(
        "-q", '--query_path',
        required=True,
        help="Input file name. Accepted formats: FASTA (.fasta, .fa) or FASTQ (.fastq, .fq)"
    )

    parser.add_argument(
        "-d", '--database',
        required=True,
        help="BLAST nucleotide database path (e.g. /path/to/nt or /path/to/slimNT)"
    )

    if len(sys.argv) <= 1:
        sys.argv.append('--help')

    global_state.iterations = parser.parse_args().iterations
    global_state.sample_size = parser.parse_args().sample_size
    global_state.tax_depth = parser.parse_args().tax_depth
    global_state.query_path = parser.parse_args().query_path
    global_state.database = parser.parse_args().database
    
    options = parser.parse_args()

    return options

def validate_query_file(query_path: str):
    """
    Check input file existence, file extension, format, and content(header, sequence).
    """

    valid_nucleotide_regex = re.compile(r'^[ACGTUNRYKMSWBDHVacgtunrykmswbdhv]+$') #Including IUPAC ambiguity codes

    # File existence
    if not os.path.isfile(query_path):
        raise FileNotFoundError(f"Input file not found: {query_path}")

    # File extension
    valid_extensions = {".fastq", ".fq", ".fasta", ".fa"}
    _, ext = os.path.splitext(query_path)
    if ext.lower() not in valid_extensions:
        raise ValueError(
            f"Unsupported input file format '{ext}'. "
            f"CensusScope only accepts FASTA or FASTQ files. "
            f"({', '.join(sorted(valid_extensions))})."
        )

    # Read first non-empty line to detect format
    try:
        with open(query_path, "r") as f:
            first_line = ""
            for line in f:
                first_line = line.strip()
                if first_line:
                    break
    except OSError as e:
        raise ValueError(f"Could not read input file '{query_path}': {e}")

    if not first_line:
        raise ValueError(f"Input file '{query_path}' is empty.")

    if first_line.startswith(">"):
        detected_format = "FASTA"

        with open(query_path, "r") as f:
            expecting_sequence = False
            record_count = 0
            current_header = None

            for line_num, line in enumerate(f, start=1):
                stripped = line.strip()

                if not stripped:
                    continue

                if stripped.startswith(">"):
                    if expecting_sequence:
                        raise ValueError(
                            f"Invalid FASTA file '{query_path}': "
                            f"header '{current_header}' has no sequence. "
                            f"Please check your input file and make sure every '>' header "
                            f"is followed by a valid nucleotide sequence."
                        )

                    record_count += 1
                    expecting_sequence = True

                else:
                    if record_count == 0:
                        raise ValueError(
                            f"Invalid FASTA file '{query_path}': "
                            f"sequence found before any '>' header at line {line_num}."
                        )

                    if not valid_nucleotide_regex.fullmatch(stripped):
                        raise ValueError(
                            f"Invalid FASTA file '{query_path}': "
                            f"invalid sequence at line {line_num}. "
                            f"Only valid nucleotide characters are allowed."
                        )

                    expecting_sequence = False

            if record_count == 0:
                raise ValueError(f"Invalid FASTA file '{query_path}': no FASTA records found.")

            if expecting_sequence:
                raise ValueError(
                    f"Invalid FASTA file '{query_path}': "
                    f"last header has no sequence. "
                    f"Please check your input file."
                )

    elif first_line.startswith("@"):
        detected_format = "FASTQ"

        with open(query_path, "r") as f:
            record_num = 0

            while True:
                header = f.readline()
                if not header:
                    break

                if not header.strip():
                    continue

                seq = f.readline()
                plus = f.readline()
                qual = f.readline()

                record_num += 1

                if not seq or not plus or not qual:
                    raise ValueError(
                        f"Invalid FASTQ file '{query_path}': incomplete record at record {record_num}."
                    )

                header = header.rstrip("\n\r")
                seq = seq.rstrip("\n\r")
                plus = plus.rstrip("\n\r")
                qual = qual.rstrip("\n\r")

                if not header.startswith("@"):
                    raise ValueError(
                        f"Invalid FASTQ file '{query_path}': "
                        f"record {record_num} header does not start with '@'."
                    )

                if not seq:
                    raise ValueError(
                        f"Invalid FASTQ file '{query_path}': "
                        f"record {record_num} has empty sequence."
                    )

                if not valid_nucleotide_regex.fullmatch(seq):
                    raise ValueError(
                        f"Invalid FASTQ file '{query_path}': "
                        f"record {record_num} contains invalid nucleotide characters."
                    )

                if not plus.startswith("+"):
                    raise ValueError(
                        f"Invalid FASTQ file '{query_path}': "
                        f"record {record_num} third line does not start with '+'."
                    )

                if len(seq) != len(qual):
                    raise ValueError(
                        f"Invalid FASTQ file '{query_path}': "
                        f"record {record_num} sequence length ({len(seq)}) does not match "
                        f"quality length ({len(qual)})."
                    )

            if record_num == 0:
                raise ValueError(f"Invalid FASTQ file '{query_path}': no records found.")

    else:
        head_char = first_line[:1]
        raise ValueError(
            f"Input file '{query_path}' does not appear to be a valid FASTA or FASTQ file. "
            f"Expected first character '>' (FASTA) or '@' (FASTQ), got '{head_char}'. "
            f"Please check the file contents."
        )

    logger.info(
        f"Input file validated: {query_path} "
        f"(extension: {ext}, detected format: {detected_format})"
    )

def validate_database(database: str):
    """
    Validate that the given path points to a usable BLAST nucleotide database
    by checking for the required core index files for the provided database prefix(e.g. SlimNT, RefSeq, nt).
    """
    valid_db_extensions = {".nsi", ".nsd", ".nin", ".nsq", ".nhr"}

    db_dir = os.path.dirname(database)
    db_prefix = os.path.basename(database)

    if not os.path.isdir(db_dir):
        raise ValueError(f"Database directory not found: {db_dir}")

    # find files that match prefix/extension
    found = [
        f for f in os.listdir(db_dir)
        if f.startswith(db_prefix) and any(f.endswith(ext) for ext in valid_db_extensions)
    ]

    if not found:
        raise ValueError(
            f"No valid BLAST database files found for prefix '{db_prefix}' in '{db_dir}'. "
            f"Expected files like: {db_prefix}.* with extensions "
            f"{', '.join(sorted(valid_db_extensions))}."
        )

    logger.info(
        f"Database validated: {database} "
        f"(found files: {', '.join(found[:5])}{'...' if len(found) > 5 else ''})"
    )

def count_sequences(query_path: str) -> int:
    """
    Use grep to count the number of sequences in a file.
    """
    logger.warning(f"    Counting sequences in {query_path}")
    try:
        result = subprocess.run(['grep', '-c', '>', query_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        count = int(result.stdout.strip())
        logger.warning(f"    {count} sequences in {query_path}")
        return count
    except subprocess.CalledProcessError as e:
        logger.error(f"Error counting sequences: {e}")
        raise ValueError(f"Error counting sequences: {e}")
    logger.warning(" ")

def sample_randomizer(iteration_count: int, query_path: str, sample_size: int):
    """
    Sample random sequences from a large FASTA or FASTQ file using awk to extract sequences.
    """

    random_samples_path = global_state.temp_dirs["random_samples"]

    logger.warning(f"Step 1: Determining how many reads we have")
    total_reads = count_sequences(query_path)  # Assuming count_sequences uses grep to count headers
    logger.warning(f"    {total_reads} FASTA records")

    if total_reads > sample_size:
        logger.info("Subset file")
        logger.warning("Step 2: Generate random sample indices for each iteration (these are read indices, not line indices)")

        for it in range(1, iteration_count + 1):
            logger.info(f"{it}- out of {iteration_count}: ")

            sample_indices = random.sample(range(total_reads), sample_size)
            sample_indices.sort()
            logger.info(f"Sample indices (sorted): {sample_indices}")

            # Create an awk script that will extract sequences based on sample_indices
            # We store the indices in an associative array
            awk_script = f"""BEGIN {{ split("{','.join(map(str, sample_indices))}", samples, ","); for (i in samples) sample_map[samples[i]] = 1 }}
            /^>/ {{ n++; if (n in sample_map) {{ print; while (getline && !/^>/) print }} }}"""

            # Use awk to extract the sequences in one go
            awk_command = f"awk '{awk_script}' {query_path} > {random_samples_path}/random_sample.{it}.fasta"

            try:
                logger.info(awk_command)
                subprocess.run(awk_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                logger.exception(f"Error during awk execution: {e}")

    else:
        logger.warning("Whole file requested, no iterations.")
        subprocess.run(f"cp {query_path} " + global_state.temp_dirs["random_samples"], shell=True)
    logger.warning("")


def blastn(database):
    """Run BLAST
    Options:
        -outfmt 6 -num_threads 10 -evalue 1e-6 -max_target_seqs 10 -perc_identity 80 -max_hsps 1
    """

    random_samples_path = global_state.temp_dirs["random_samples"]
    blastn_path =  global_state.temp_dirs["blastn"]
    filenames = next(os.walk(random_samples_path), (None, None, []))[2]
    for random_sample in filenames:
        now = datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z')
        identifier = random_sample.split(".")[1]
        output = f"{blastn_path}/result_{identifier}.txt"
        
        blast_command = (
            f"blastn -db {database} "
            f"-query {random_samples_path}/{random_sample} -out {output} -outfmt 6 "
            f"-num_threads 10 -evalue 1e-6 -max_target_seqs 10 -perc_identity 80 -max_hsps 1"
        )

        logger.info(f"{now}: Start result_{identifier}.txt\n\t{blast_command}")
        subprocess.run(blast_command, shell=True)
        logger.warning(f"Finished blastn for {random_sample}, output is result_{identifier}.txt")
        logger.info(datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z'))

def refine_blast_files(sample_size: int):
    """
    Iterate over all blast result files, process each one.
    Use multithreading to process multiple files concurrently.
    Track hit counts across all files and calculate averages.
    """
    logger.warning("----------------------")
    logger.warning("Refining BLAST results")
    logger.info(datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z'))
    blastn_path =  global_state.temp_dirs["blastn"]
    blast_results = next(os.walk(blastn_path), (None, None, []))[2]
    overall_hits = defaultdict(list)  # A dictionary to track hits for each accession across files
    unique_accessions = []

    for result_file in blast_results:
        if "result" not in result_file:
            continue
        unique_reads = set()
        tax_data = defaultdict(int)
        iteration_hits = 0

        with open(f"{blastn_path}/{result_file}", "r") as blast_file:
            reader = csv.reader(blast_file, delimiter="\t")
            for row in reader:
                read_id = row[0]
                if "|" in row[1]:
                    try:
                        accession_raw = row[1].split("|")[3]
                    except IndexError as error:
                        accession_raw = row[1].split("|")[-1]
                else:
                    accession_raw = row[1]

                accession = normalize_accession(accession_raw)

                if accession not in unique_accessions:
                    unique_accessions.append(accession)

                if read_id not in unique_reads:
                    unique_reads.add(read_id)
                    tax_data[accession] += 1
                    iteration_hits += 1

            tax_data["unaligned"] = sample_size - iteration_hits

        for accession, hit_count in tax_data.items():
            if hit_count == 0 and accession != "unaligned":
                logger.warning(f"Zero hit count for accession '{accession}'")
            overall_hits[accession].append(hit_count)

    tax_tree = fetch_taxonomy(unique_accessions)
    write_final_table(overall_hits, tax_tree)


def fetch_taxonomy(unique_accessions: dict): 
    """This query retrieves the full taxonomic lineage for a given accession.
    It uses a recursive Common Table Expression (CTE) to traverse the 
    taxonomic hierarchy from the accession's associated taxid up to the 
    root. The `lineage` CTE starts with the initial taxid and iteratively 
    joins the `nodes` table to find parent taxids, building the lineage 
    path while preventing cycles. The query includes a `depth` column to track 
    recursion levels, ensuring correct lineage order. The final result is 
    ordered by depth to reflect the hierarchical structure from the starting 
    taxid up to the root.
    """
    
    db_file = '/app/blastdb/taxonomy.db'
    tax_tree = {
        "0": {
            "taxid": 0,
            "name": "unmatched",
            "rank": None,
            "children": None,
            "accessions": []
	    }
    }
    nodes = {}

    if os.path.isfile(db_file):
        taxonomy_conn = sqlite3.connect(db_file)
    else:
        logger.error("No taxonomy DB found. Taxonomic rankings will be ignored.")
        for accession in unique_accessions:
            tax_tree["0"]["accessions"].append(accession)
        return tax_tree

    cursor = taxonomy_conn.cursor()
    query = """
    WITH RECURSIVE lineage(taxid, name, rank, parent_taxid, path, depth) AS (
        -- Start with the taxid associated with the given accession
        SELECT n.taxid, na.name, n.rank, n.parent_taxid, n.taxid || ',' AS path, 0 AS depth
        FROM accession_taxid a
        JOIN nodes n ON a.taxid = n.taxid
        JOIN names na ON n.taxid = na.taxid
        WHERE a.accession = ?

        UNION ALL

        -- Recursively join the nodes table to traverse up the hierarchy
        SELECT n.taxid, na.name, n.rank, n.parent_taxid, l.path || n.taxid || ',', l.depth + 1
        FROM nodes n
        JOIN names na ON n.taxid = na.taxid
        JOIN lineage l ON n.taxid = l.parent_taxid
        -- Prevent cycles by checking if the taxid has already been visited
        WHERE instr(l.path, n.taxid || ',') = 0
    )
    -- Select the lineage in reverse hierarchical order
    SELECT taxid, name, rank, parent_taxid
    FROM lineage
    ORDER BY depth DESC;
    """

    json_file = global_state.temp_dirs['results'] + "/tax_tree.json"
    for accession in unique_accessions:
        cursor.execute(query, (accession,))
        lineage = cursor.fetchall()
        if len(lineage) < 1:
            tax_tree["0"]["accessions"].append(accession)
        else: 
            add_to_tree(tax_tree, lineage, accession)
    taxonomy_conn.close()
    json_object = json.dumps(tax_tree, indent=4)
 
    # Writing to sample.json
    with open(json_file, "w") as outfile:
        outfile.write(json_object)

    return tax_tree 


global_tax_tree = {}
orphans = {}

def find_or_create_node(tax_tree, taxid, name, rank, parent_taxid):
    if taxid in global_tax_tree:
        return global_tax_tree[taxid]

    new_node = {
        "taxid": taxid,
        "parent": parent_taxid,
        "name": name,
        "rank": rank,
        "children": {},
    }
    global_tax_tree[taxid] = new_node

    if parent_taxid in global_tax_tree:
        global_tax_tree[parent_taxid]["children"][taxid] = new_node
    else:
        orphans.setdefault(parent_taxid, []).append(taxid)
        tax_tree[taxid] = new_node  # Temporarily place it in the main tree

    return new_node


def handle_orphans(parent_taxid):
    if parent_taxid in orphans:
        parent_node = global_tax_tree[parent_taxid]
        for orphan_taxid in orphans[parent_taxid]:
            parent_node["children"][orphan_taxid] = global_tax_tree[orphan_taxid]
        del orphans[parent_taxid]


def add_to_tree(tax_tree, lineage, accession):
    tax_depth = global_state.tax_depth

    for taxid, name, rank, parent_taxid in lineage:
        if taxid in {1, 131567}:
            continue

        if rank == '-':
            continue

        node = find_or_create_node(tax_tree, taxid, name, rank, parent_taxid)
        handle_orphans(taxid)  # Check for and reattach orphans

        if rank == tax_depth:
            node.setdefault("accessions", []).append(accession)
            break


def traverse_tax_tree(node, overall_hits, final_table, total_hits, lineage=""):
    taxid = node.get('taxid')
    name = node.get('name')
    accessions = node.get('accessions', [])
    children = node.get('children', {})

    # Build the current lineage string
    current_lineage = f"{lineage}; {name}" if lineage else name

    # Process accessions if present
    if accessions:
        if node["name"] == "unmatched":
            unmatched_sum = 0
            unmatched_iterations = 0
            for accession in node["accessions"]:
                unmatched_sum += sum(overall_hits[accession])
                if len(overall_hits[accession]) > unmatched_iterations:
                    unmatched_iterations = len(overall_hits[accession])
        else:
            hit_sum = 0
            iterations_present = 0

            for accession in accessions:
                if accession in overall_hits:
                    hit_sum += sum(overall_hits[accession])  # Total hits for this accession
                    if len(overall_hits[accession]) > iterations_present:
                        iterations_present = len(overall_hits[accession])  # Number of iterations for this accession
            
            # Calculate average hits (percentage of total hits)
            average_hits = round(hit_sum / total_hits, 4) if total_hits > 0 else 0

            # Add row to the final table
            final_table.append([
                taxid,          # Taxonomy ID
                name,           # Taxonomic Name
                average_hits,   # Percentage (average hits / total hits)
                hit_sum,        # Total Hits
                iterations_present,  # Iterations Present
                current_lineage  # Full Lineage
            ])

    # Recursively process children
    if children:
        for child_taxid, child_node in children.items():
            traverse_tax_tree(child_node, overall_hits, final_table, total_hits, current_lineage)


def write_final_table(overall_hits, tax_tree):
    """
    Calculate the average hit count for each GB accession and write the final output.
    # TODO: iterations will cease if no new organizm is found - OPTIONAL 
    """
    logger.warning("Writing final results")
    logger.info(datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z'))
    results_path = global_state.temp_dirs["results"]
    total_hits = sum([sum(hits) for hits in overall_hits.values()])  # Total hits across all accessions
    taxonomy_table = []
    accession_table = []

    for accession, hits in overall_hits.items():

        hit_sum = sum(hits)
        iterations_present = len(hits)
        average_hits = round(hit_sum / total_hits, 4)
        accession_table.append([accession, hit_sum, iterations_present, average_hits])

    with open(f"{results_path}/accession_table.tsv", "w", newline="") as accession_file:
        writer = csv.writer(accession_file, delimiter="\t")
        writer.writerow(["Accession", "Total Hits", "Iterations Present", "Average Hits"])
        writer.writerows(accession_table)

    if len(tax_tree.keys()):
        for taxid, node in tax_tree.items():
            traverse_tax_tree(node, overall_hits, taxonomy_table, total_hits)
    
    with open(f"{results_path}/taxonomy_table.tsv", "w", newline='') as final_file:
        writer = csv.writer(final_file, delimiter="\t")
        writer.writerow(["Taxid", "Name", "Percentage", "Total Hits", "Iterations Present", "Full Lineage"])
        writer.writerows(taxonomy_table)


def fastq_to_fasta(query_path):
    """
    Use grep to get the first character of the first line in the file.
    Determine the file format (FASTA or FASTQ)
    If format is FASTQ then convert to a FASTA and stort in a temp file.
    This uses the seqtk (https://github.com/lh3/seqtk) program. 
    """

    output_fasta = global_state.temp_dirs["inputs"]+"/temp.fasta"
    head_command = f"head -n 1 {query_path} | cut -c1"
    try:
        head_char = subprocess.run(
            head_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.exception(f"Error counting sequences: {e}")
        return 0

    if head_char == ">":
        return query_path

    elif head_char == "@":
        try:
            subprocess.run(f"seqtk seq -a {query_path} > {output_fasta}", shell=True, check=True)
            logger.warning(f"Conversion from FASTA to FASTQ complete: {output_fasta}")
            return output_fasta
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error during conversion: {e}")

    else:
        logger.critical(f"Unknown file format {head_char}")
        raise ValueError(f"Unsupported sequence header format: {head_char}")
        

def main():
    """
    Main function
    """
    
    logger.info("FileHandler created successfully.")
    options = usr_args()
    logger.info(f"{options}")
    logger.warning("")

    try:
        validate_query_file(global_state.query_path)
    except (ValueError, FileNotFoundError) as e:
        logger.critical(f"Input validation failed: {e}")
        sys.exit(1)

    try:
	    validate_database(global_state.database)
    except ValueError as e:
        logger.critical(f"Database validation failed: {e}")
        sys.exit(1)

    global_state.query_path = fastq_to_fasta(
        query_path=global_state.query_path
    )

    sample_randomizer(
        iteration_count=int(global_state.iterations),
        query_path = global_state.query_path,
        sample_size=int(options.sample_size)
    )
    
    blastn(
        database=options.database
    )
    
    refine_blast_files(
        sample_size=int(options.sample_size)
    )
    

if __name__ == "__main__":
    main()
