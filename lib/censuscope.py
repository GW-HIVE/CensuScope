#!/usr/bin/env python3
"""
"""

import argparse
import concurrent.futures
import csv
import json
import os
import logging
import random
import requests
import shutil
import subprocess
import sqlite3
from sqlite3 import Error
import sys
import time
import xml.etree.ElementTree as ET 
from collections import defaultdict
from datetime import datetime
from threading import Thread, Lock
from urllib.parse import urlparse

write_lock = Lock()

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
log_file_path = os.path.join(global_state.temp_dirs["results"], "censuscope.log")

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(log_file_path)
stream_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.info(
    "#_______________________________________________________________________________________________________#\n"+
    "Global State values set: "+
    f"\n\tStart Time: {global_state.start_time},\n\tBase directory: {global_state.base_dir}, \n\tTemp path: {global_state.temp_path}"
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

        for it in range(1, iteration_count + 1):
            logger.info(f"{it}- out of {iteration_count}")

            "Step 2: Generate random sample indices (these are read indices, not line indices)"
            sample_indices = random.sample(range(total_reads), sample_size)
            sample_indices.sort()
            logger.info(f"Sample indices (sorted): {sample_indices}")

            # Step 3: Create an awk script that will extract sequences based on sample_indices
            # We store the indices in an associative array
            awk_script = f"""BEGIN {{ split("{','.join(map(str, sample_indices))}", samples, ","); for (i in samples) sample_map[samples[i]] = 1 }}
            /^>/ {{ n++; if (n in sample_map) {{ print; while (getline && !/^>/) print }} }}"""

            # Use awk to extract the sequences in one go
            awk_command = f"awk '{awk_script}' {query_path} > {random_samples_path}/random_sample.{it}.fasta"

            try:
                subprocess.run(awk_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                logger.exception(f"Error during awk execution: {e}")

    else:
        logger.info("Whole file")
        subprocess.run(f"cp {query_path} home/random_samples/random_sample.1.fasta", shell=True)


def blastn(query_path, database):
    """"""
    random_samples_path = global_state.temp_dirs["random_samples"]
    blastn_path =  global_state.temp_dirs["blastn"]
    filenames = next(os.walk(random_samples_path), (None, None, []))[2]
    for random_sample in filenames:
        identifier = random_sample.split(".")[1]
        output = f"{blastn_path}/result_{identifier}.txt"
        
        blast_command = (
            f"blastn -db {database} "
            f"-query {random_samples_path}/{random_sample} -out {output} -outfmt 6 "
            f"-num_threads 10 -evalue 1e-6 -max_target_seqs 10 -perc_identity 80 -max_hsps 1"
        )

        subprocess.run(blast_command, shell=True)


def refine_blast_files(sample_size: int):
    """
    Iterate over all blast result files, process each one.
    Use multithreading to process multiple files concurrently.
    Track hit counts across all files and calculate averages.
    """

    blastn_path =  global_state.temp_dirs["blastn"]
    results_path = global_state.temp_dirs["results"]
    blast_results = next(os.walk(blastn_path), (None, None, []))[2]
    overall_hits = defaultdict(list)  # A dictionary to track hits for each accession across files
    unique_accessions = []

    for result_file in blast_results:
        if "result" not in result_file:
            continue
        unique_reads = set()
        filtered_data = []
        tax_data = defaultdict(int)
        unaligned_reads = sample_size
        identifier = result_file.split("_")[1].split(".")[0]
        iteration = f"{results_path}/iteration{identifier}.tsv"
        refine_name = f"{results_path}/refined.{identifier}.tsv"
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
                    # found_unique_accessions = True

                if read_id not in unique_reads:
                    unique_reads.add(read_id)
                    filtered_data.append(row)
                    tax_data[accession] += 1
                    iteration_hits += 1

            tax_data["unaligned"] = sample_size - iteration_hits
        for accession, hit_count in tax_data.items():
            if hit_count == 0:
                import pdb; pdb.set_trace()
            overall_hits[accession].append(hit_count)

        with open(refine_name, "w", newline='') as refined_file:
            writer = csv.writer(refined_file, delimiter="\t")
            writer.writerows(filtered_data)

        with open(iteration, "w", newline='') as iteration_file:
            writer = csv.writer(iteration_file, delimiter="\t")
            for accession, count in tax_data.items():
                writer.writerow([accession, count])
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
        logger.error("No SQLite DB to check")
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
    SELECT taxid, name, rank, parent_taxid, depth
    FROM lineage
    ORDER BY depth DESC;
    """

    for accession in unique_accessions:
        cursor.execute(query, (accession,))
        lineage = cursor.fetchall()
        if len(lineage) < 1:
            tax_tree["0"]["accessions"].append(accession)
        else: 
            add_to_tree(tax_tree, lineage, accession, max_depth=6)
    taxonomy_conn.close()

    return tax_tree 


def add_to_tree(tax_tree: dict, lineage: list, accession: str, max_depth: int):
    """Recursively adds nodes to the tree for each taxonomic lineage."""
    current_level = tax_tree
    tax_key = None  # To keep track of the taxid at max_depth
    for taxid, name, rank, parent_taxid, depth in lineage:
        # Skip the root node if needed
        # if taxid == 1:
        #     lineage.pop(0)
        
        # if taxid == 131567:
        #     lineage.pop(0)
        # print(lineage, "\n")
        # Create or update the current node
        if taxid not in current_level and depth > max_depth:
            current_level[taxid] = {
                "taxid": taxid,
                "name": name,
                "rank": rank,
                "depth": depth,
                "children": {},
                # "accessions": [] if depth == max_depth else None  # Initialize list only at max_depth
            }
        
            current_level = current_level[taxid]["children"]

        # If at max_depth, keep track of this taxid for appending the accession
        if depth == max_depth:
            tax_key = taxid
            current_level[taxid] = {
                "taxid": taxid,
                "name": name,
                "rank": rank,
                "depth": depth,
                "accessions": [accession]
            }

        if depth <= max_depth:
            current_level[tax_key]["accessions"].append(accession)


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
    # TODO: Need percentage of reads are comming from each accessions.. Composition of sample
    # TODO: how many accessions are from each organizm => Tax tree
    # TODO: iterations will cease if no new organizm is found - OPTIONAL 
    """
    
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


    options.query_path = fastq_to_fasta(
        query_path=options.query_path
    )

    sample_randomizer(
        iteration_count=int(options.iterations),
        query_path = options.query_path,
        sample_size=int(options.sample_size)
    )
    
    blastn(
        query_path=options.query_path,
        database=options.database
    )
    
    refine_blast_files(
        sample_size=int(options.sample_size)
    )
    

if __name__ == "__main__":
    main()
