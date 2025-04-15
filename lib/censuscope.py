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

write_lock = Lock()

__version__ = "0.1"
__status__ = "BETA"


class GlobalState:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.start_time = datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z')
        # self.temp_path = f"{self.base_dir}/temp_dirs/{self.start_time}"
        self.temp_path = f"{self.base_dir}/temp_dirs"   #For debugging
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
log_file_path = os.path.join(global_state.temp_dirs["results"], "censuscope.log")

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(log_file_path)
stream_handler = logging.StreamHandler()
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
        help="Input file name"
    )

    parser.add_argument(
        "-d", '--database',
        required=True,
        help="BLAST database name"
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


def count_sequences(query_path: str) -> int:
    """
    Use grep to count the number of sequences in a file.
    """
    logger.info(f"Counting sequences in {query_path}")
    try:
        result = subprocess.run(['grep', '-c', '>', query_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        count = int(result.stdout.strip())
        logger.info(f"{count} sequences in {query_path}")
        return count
    except subprocess.CalledProcessError as e:
        logger.error(f"Error counting sequences: {e}")
        raise ValueError(f"Error counting sequences: {e}")


def sample_randomizer(iteration_count: int, query_path: str, sample_size: int):
    """
    Sample random sequences from a large FASTA or FASTQ file using awk to extract sequences.
    """

    random_samples_path = global_state.temp_dirs["random_samples"]

    logger.info(f"Step 1: Determining how many reads we have")
    total_reads = count_sequences(query_path)  # Assuming count_sequences uses grep to count headers
    logger.info(f"{total_reads} FASTA records")

    if total_reads > sample_size:
        logger.info("Subset file")
        logger.info("Step 2: Generate random sample indices for each iteration (these are read indices, not line indices)")

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
        logger.info("Whole file requested, no iterations.")
        subprocess.run(f"cp {query_path} " + global_state.temp_dirs["random_samples"], shell=True)


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
        logger.info(f"Finished result_{identifier}.txt")
        logger.info(datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H.%M.%S%z'))


def refine_blast_files(sample_size: int):
    """
    Iterate over all blast result files, process each one.
    Use multithreading to process multiple files concurrently.
    Track hit counts across all files and calculate averages.
    """

    logger.info("Refining BLAST results")
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
                        accession= row[1].split("|")[3]
                    except IndexError as error:
                        accession= row[1].split("|")[-1]
                else:
                    accession= row[1]
                
                if accession not in unique_accessions:
                    unique_accessions.append(accession)

                if read_id not in unique_reads:
                    unique_reads.add(read_id)
                    tax_data[accession] += 1
                    iteration_hits += 1

            tax_data["unaligned"] = sample_size - iteration_hits

        for accession, hit_count in tax_data.items():
            if hit_count == 0:
                logger.exception(f"Error with hit count for accession {accession}!")
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
    
    db_file = 'taxonomy.db'
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
    logger.info("Writing final results")
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
            logger.info(f"Conversion complete: {output_fasta}")
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
