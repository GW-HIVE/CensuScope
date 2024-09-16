#!/usr/bin/env python3
"""
"""

import csv
import json
import argparse
import sys
import os
import time
import random
import shutil
import subprocess
from urllib.parse import urlparse
from Bio import SeqIO

__version__ = "0.1"
__status__ = "BETA"

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
        help="number of iterations to perform"
    )

    parser.add_argument(
        "-s", '--sample-size',
        required=True,
        help="Read sample size"
    )

    parser.add_argument(
        "-t", '--tax-depth',
        required=True,
        help="Tax Depth"
    )

    parser.add_argument(
        "-q", '--query',
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


def sample_randomizer(iteration_count: int, query:str, sample_size: int):
    """
    # Initialization

    # Open the file and read first char
    # Process 
    # Get the number of lines sequences in the query file
    # Generate a list of random indexes
    # Random sampling or file copying
    """

    try:
        with open(query, 'r') as query_file:
            first_char = query_file.read(1)
            print(first_char)
    except Exception as error:
        print(f"Could not get handle: {error}")
        # break

    if first_char == ">":
        records = list(SeqIO.parse(query, "fasta"))
        total_reads = len(records)
        seq_format = "FASTA"
        print(f"{total_reads} {seq_format} records")
    elif first_char == "@":
        records = list(SeqIO.parse(query, "fastq"))
        total_reads = len(records)
        seq_format = "FASTQ"
        print(f"{total_reads} {seq_format} records")

    if total_reads > sample_size:
        print("subset file")
        for it in range(1, iteration_count + 1):
            print(f"{it}- out of {iteration_count}")
            sample_list = random.sample(range(0,total_reads), sample_size)
            with open(f"home/random_samples/random_sample.{it}.fasta", "w") as random_file:
                for sample in sample_list:
                    SeqIO.write(records[sample], random_file, "fasta")

    else:
        print("whole file")
        with open(f"home/random_samples/random_sample.1.fasta", "w") as random_file:
                for sample in records:
                    SeqIO.write(sample, random_file, "fasta")



def blastn(query, database):
    """"""
    
    filenames = next(os.walk("home/random_samples"), (None, None, []))[2]
    for random_sample in filenames:
        identifier = random_sample.split(".")[1]
        output = f"home/blastn/result_{identifier}.txt"
        
        query = (
            f"blastn -db {database} "
            f"-query home/random_samples/{random_sample} -out {output} -outfmt 10 "
            f"-num_threads 10 -evalue 1e-6 -max_target_seqs 1 -perc_identity 80"
        )

        subprocess.run(query, shell=True)

def refine():
    """
    # Read the contents of the file into a list of lines
    # Extract the first element (before the comma) of each line and store it in 'read' list
    # Get the unique elements from the 'read' list
    # Build the total string by appending lines that have a unique identifier
    # Write the total string to the refine file
    """
    
    filenames = next(os.walk("home/blastn"), (None, None, []))[2]
    
    for blast in filenames:
        read = []
        total = ""
        identifier = blast.split("_")[1].split(".")[0]
        refine_name = f"home/blastn/refined.{identifier}.txt"
        print(identifier, blast)
        with open(f"home/blastn/{blast}", "r") as blast_file:
            data = blast_file.readlines()
        for line in data:
            name = line.split(",")
            read.append(name[0])
        unique = list(dict.fromkeys(read))

        for datum in range(len(data)):
            if datum < len(unique):
                total += data[datum]
        with open(refine_name, "w") as refined_file:
            refined_file.write(total)


def main():
    """
    Main function
    """
    options = usr_args()
    iter_counter = 0
    print(options)
    time_start = time.time()
    iteration_count = int(options.iterations)

    # sample_randomizer(
    #     iteration_count=iteration_count,
    #     query = options.query,
    #     sample_size=int(options.sample_size)
    # )
    
    # blastn(
    #     query=options.query,
    #     database=options.database
    # )

    refine()
    


if __name__ == "__main__":
    main()
