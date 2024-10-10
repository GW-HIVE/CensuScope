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

        logging.info(
            "#________________________________________________________________________________#"
        )
        logging.info(
            f"Global State values set: {self.start_time}, {self.base_dir}, {self.temp_path}"
        )
global_state = GlobalState()

log_file_path = os.path.join(global_state.temp_path, "CensuScope_app.log")
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler(log_file_path),
        # logging.StreamHandler()
    ]
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

    try:
        result = subprocess.run(['grep', '-c', '>', query_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return int(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error counting sequences: {e}")


def sample_randomizer(iteration_count: int, query_path: str, sample_size: int):
    """
    Sample random sequences from a large FASTA or FASTQ file using awk to extract sequences.
    """

    random_samples_path = global_state.temp_dirs["random_samples"]

    # Step 1: Determine how many reads we have
    total_reads = count_sequences(query_path)  # Assuming count_sequences uses grep to count headers
    logging.info(f"{total_reads} FASTA records")

    if total_reads > sample_size:
        logging.info("Subset file")

        for it in range(1, iteration_count + 1):
            logging.info(f"{it}- out of {iteration_count}")

            # Step 2: Generate random sample indices (these are read indices, not line indices)
            sample_indices = random.sample(range(total_reads), sample_size)
            sample_indices.sort()
            logging.info(f"Sample indices (sorted): {sample_indices}")

            # Step 3: Create an awk script that will extract sequences based on sample_indices
            # We store the indices in an associative array
            awk_script = f"""BEGIN {{ split("{','.join(map(str, sample_indices))}", samples, ","); for (i in samples) sample_map[samples[i]] = 1 }}
            /^>/ {{ n++; if (n in sample_map) {{ print; while (getline && !/^>/) print }} }}"""

            # Use awk to extract the sequences in one go
            awk_command = f"awk '{awk_script}' {query_path} > {random_samples_path}/random_sample.{it}.fasta"

            try:
                subprocess.run(awk_command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                logging.exception(f"Error during awk execution: {e}")

    else:
        logging.info("Whole file")
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
        total_hits = 0

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
                    total_hits += 1
            tax_data["unaligned"] = sample_size - total_hits
        for accession, hit_count in tax_data.items():
            overall_hits[accession].append(hit_count)

        with open(refine_name, "w", newline='') as refined_file:
            writer = csv.writer(refined_file, delimiter="\t")
            writer.writerows(filtered_data)

        with open(iteration, "w", newline='') as iteration_file:
            writer = csv.writer(iteration_file, delimiter="\t")
            for accession, count in tax_data.items():
                writer.writerow([accession, count])
    accession2uid = fetch_nucleotide_uids(unique_accessions)
    print(accession2uid)
    write_final_table(overall_hits, unique_accessions)


def fetch_nucleotide_uids(unique_accessions: list):
    """
    Get UIDs from Nucleotide Accessions
    """
    
    tax_tree = {}
    unique_gi = []
    accession2uid = []
    esearch_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"


    for i in range(0, len(unique_accessions), 20):
        x = i 
        terms = ",".join(unique_accessions[x:x+20])
        esearch_url = f"{esearch_base_url}db=nucleotide&term={terms}&retmode=json"
        try:
            response = requests.get(esearch_url)
            if response.status_code == 200:
                esearch_result = json.loads(response.content.decode("utf-8"))
                unique_gi.extend(esearch_result["esearchresult"]["idlist"])

        except Exception as e:
            print(f"Error fetching  UIDs for {terms}: {e}")
            import pdb; pdb.set_trace()
    accession2uid = list(zip(unique_accessions, unique_gi))
    fetch_taxonomy_info(unique_gi)
    
    return accession2uid


def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def fetch_taxonomy_info(uid: str):
    """
    Fetch taxonomy info from NCBI for the given accession number.
    """
    
    elink_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?"
    elink_url = f"{elink_base_url}dbfrom=nucleotide&db=taxonomy&id={uid}"
    try:
        response = requests.get(elink_url)
        if response.status_code == 200:
            elink_xml = ET.XML(response.content.decode("utf-8"))
            elink_result = etree_to_dict(elink_xml)
            print(elink_result)
        else:
            import pdb; pdb.set_trace()
    except Exception as e:
        print(f"Error fetching taxonomy ID for {id_list}: {e}")


    
def write_final_table(overall_hits, unique_accessions):
    """
    Calculate the average hit count for each GB accession and write the final output.
    """
    
    results_path = global_state.temp_dirs["results"]
    total_hits = sum([sum(hits) for hits in overall_hits.values()])  # Total hits across all accessions

    final_table = []

    for accession, hits in overall_hits.items():
        hit_sum = sum(hits)
        iterations_present = len(hits)
        average_hits = round(hit_sum / total_hits, 4) if total_hits > 0 else 0
        final_table.append([accession, hit_sum, iterations_present, average_hits])
    
    # TODO: Need percentage of reads are comming from each accessions.. Composition of sample
    # TODO: how many accessions are from each organizm => Tax tree
    # TODO: iterations will cease if no new organizm is found - OPTIONAL 

    # Write the final table to a file
    with open(f"{results_path}/final_table.tsv", "w", newline='') as final_file:
        writer = csv.writer(final_file, delimiter="\t")
        writer.writerow(["Accession", "Total Hits", "Iterations Present", "Average Hits"])
        writer.writerows(final_table)


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
        logging.exception(f"Error counting sequences: {e}")
        return 0

    
    if head_char == ">":
        return query_path

    elif head_char == "@":
        try:
            subprocess.run(f"seqtk seq -a {query_path} > {output_fasta}", shell=True, check=True)
            logging.info(f"Conversion complete: {output_fasta}")
            return output_fasta
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error during conversion: {e}")

    else:
        logging.critical(f"Unknown file format {head_char}")
        raise ValueError(f"Unsupported sequence header format: {head_char}")
        

def main():
    """
    Main function
    """

    options = usr_args()

    options.query_path = fastq_to_fasta(
        query_path=options.query_path
    )

    # sample_randomizer(
    #     iteration_count=int(options.iterations),
    #     query_path = options.query_path,
    #     sample_size=int(options.sample_size)
    # )
    
    # blastn(
    #     query_path=options.query_path,
    #     database=options.database
    # )

    refine_blast_files(
        sample_size=int(options.sample_size)
    )
    


if __name__ == "__main__":
    main()
