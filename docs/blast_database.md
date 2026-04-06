# BLAST Database

This README document describes the BLAST database used by CensuScope: what it is, how it is used, and how to build it. The BLAST database is treated as **external, static reference data** and is not modified during execution. This file is a **required** input file for the CensuScope Docker. 

---

## Table of Contents
1. [Purpose](#purpose)
2. [CensuScope Core Components](#censuscope-core-components)
3. [Locating a BLAST Database](#locating-a-blast-database) -> Step-by-step Instructions
4. [Relationship to taxonomy.db](#relationship-to-taxonomydb)
5. [Next Steps](#next-steps)


---

## Purpose

The BLAST database serves as the reference against which sequencing reads are aligned during CensuScope execution.

It is used for:
- aligning sampled reads using BLAST
- identifying candidate organisms present in the input data
- generating taxonomic signals for downstream aggregation

The BLAST database is:
- user-provided
- built externally using standard BLAST tools
- reusable across multiple runs and analyses

CensuScope treats the BLAST database as **read-only input** during runtime.

---

## CensuScope Core Components

CensuScope relies on three primary inputs:

### FASTQ Input (Dynamic)
- User-provided sequencing reads in FASTQ format
- Varies between runs
- Randomly sampled during execution
- Primary source of variability in results
- Referred to in documentation as QUERY_FILE

### ‼️ BLAST Database (Static)
- User-provided nucleotide database
- Built prior to execution
- Shared across runs
- Used as a fixed reference for alignment

### Taxonomy Database (`taxonomy.db`) (Static)
- User-provided SQLite database
- Prebuilt SQLite database containing taxonomic hierarchy and names
- Built prior to execution or provided with the Docker image
- Used to map BLAST results to taxonomic identifiers
- Enables aggregation and labeling of results across taxonomic ranks

To build the **taxonomy.db** file, please refer to this [README](https://github.com/GW-HIVE/CensuScope/blob/main/docs/taxonomydb.md) called [taxonomydb.md](https://github.com/GW-HIVE/CensuScope/blob/main/docs/taxonomydb.md).

---

## Locating a BLAST Database

BLAST databases must be created **before running CensuScope**. In this context, the BLAST database is a FASTA file (`.fa`) that contains many nucleotide sequences combined into a single file and serves as the reference for alignment.

Users can generate this file themselves or use existing resources such as the NCBI NT database or our lab’s SlimNT repository.

### Locating a Database

A BLAST database file can be either created by the user or obtained from existing resources. In this context, the BLAST database is a FASTA file (`.fa`) that contains many nucleotide sequences combined into a single reference file.

Common examples of BLAST databases include those provided by NCBI (e.g., `nt`, `refseq_genomes`), which are also available as selectable options in the [BLASTN web interface](https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&BLAST_SPEC=GeoBlast&PAGE_TYPE=BlastSearch). These databases represent the types of reference collections typically used or emulated in CensuScope workflows.

Common options include:

- **NCBI NT database** (standard, comprehensive)
  - Use NCBI's [FTP BLAST Site](https://ftp.ncbi.nlm.nih.gov/blast/db/) to locate and download BLAST database files, including NT.
- **SlimNT** (curated, reduced database)
  - The GitHub Repo to create or download `slimNT.fa` can be found [here](https://github.com/GW-HIVE/slimNT).
- **Filtered NT** (lab-specific filtered database)
  - The GitHub Repo to create or download `filter_nt.fa` can be found [here](https://github.com/GW-HIVE/filtered_nt).

> Note: Larger databases improve coverage but increase runtime and resource usage.

---

### Install BLAST

Install BLAST+ from NCBI if not already available on your computer:
```
https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/
```

Verify `makeblastdb` installation:
```
makeblastdb -version
```

---

### Build the Database

In order for CensuScope to use the BLAST reference, the FASTA file must be converted into an NCBI-recognized BLAST database using `makeblastdb`.

If you have already cloned this CensuScope repository, first create the required directories, under the CensuScope directory:

```
mkdir -p {inputs,temp_dirs,database}
chmod 777 temp_dirs
```

Move your BLAST FASTA file (e.g., `slimNT.fa`) into the `database/` directory, then navigate into it:
```
cd database
```

Run `makeblastdb` to create the BLAST database:
```
makeblastdb -in BLAST_db_file.fa -dbtype nucl -out my_blast_db
```
Specific Example:
```
makeblastdb -in slimNT.fa -dbtype nucl -out slimNT/
```

This will generate files such as, which appear in a subdirectory your "-out" flag points to:

- `my_blast_db.nsq`
- `my_blast_db.nin`
- `my_blast_db.nhr`

These files collectively represent the BLAST database. This filepath will be the input to "--database" flag in your future `docker run` command.

Note: The files created may separate into the `slimNT/` subdirectory and some in the `database/' subdirectory. The filepath for "--database" flag would point to the location that the **.nsq**, **.nin**, and **.nhr** files are located.

### Notes on Build Time

- Building large databases (e.g., NT) can take **hours to days**
- Disk space requirements can be **hundreds of GB**
- Plan accordingly before starting
  
---

## Relationship to taxonomy.db

CensuScope uses both:

- **BLAST database** → performs sequence alignment  
- **taxonomy.db** → maps results to taxonomy  

Both must be prepared **before execution** and are treated as **read-only inputs**. 
The `taxonomy.db` file contains the taxonomic information required to build the taxonomy tree and organize results by taxonomic rank. It is used to map BLAST alignment results to taxonomic identifiers and generate structured output.

The BLAST database is a FASTA-based reference that CensuScope uses to align input sequencing reads. This alignment step enables metagenomic identification of organisms present in the sample.

If a genome or sequence is not present in the BLAST database, reads originating from that organism will not align and may be reported as `unaligned` or `no_match`.

--- 

## Next Steps

Once your BLAST database is built:

- If you still need to build `taxonomy.db`, follow the taxonomy database [README](https://github.com/GW-HIVE/CensuScope/blob/main/docs/taxonomydb.md). 
- If both databases are ready, proceed to the CensuScope Docker or CLI execution guide.
