# CensuScope Docker Deployment
## Contents
- [Requirements](#requirements)
- [Running via the command line](#running-via-the-command-line) -> Step-by-step Directions
- [Building CensuScope via Docker](#building-censuscope-via-docker)
- [Running the container via Docker](#running-the-container-via-docker)
- [Pushing a new build to GitHub](#pushing-a-new-build-to-github)
  
## Requirements
Software requirements needed to run the CensuScope Docker include:
1. Python ≥3.10.6. [3.10.6 recommended](https://www.python.org/downloads/release/python-3106/) (for command line use or development)
2. [Docker](https://docs.docker.com/engine/install/)
    - Links if using Docker Desktop:
      - [Docker Desktop for Linux](https://docs.docker.com/desktop/install/linux-install/)
      - [Docker Desktop for Mac (macOS)](https://docs.docker.com/desktop/install/mac-install/)
      - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
3. [NCBI Blast Command Line tool](https://www.ncbi.nlm.nih.gov/books/NBK569856/)
4. Database: An indexed database and optional taxonomy map (recommend doing this in your home directory or somewhere you have full permissions)
     * Look to [taxonomy.db](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/taxonomydb.md) and [blast_database.md](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/blast_database.md) README's for more information.
<br>

## Running via the command line
### Clone the repository
```
git clone https://github.com/GW-HIVE/CensuScope/
```
### Enter the repository
```
cd CensuScope
```

**Make sure you are on the desired branch (Check for latest branch):**

```
git switch [DESIRED BRANCH TAG]
```
or 
```
git fetch origin
```
```
git checkout BRANCH_NAME
```

### Build project folders
```
mkdir -p {inputs,temp_dirs,database}
chmod 777 temp_dirs
```
1. Move your query file (sample file) into the `inputs` directory and name appropriately (the command calls `QUERY.FILE`).
2. Move your **database** file (e.g., slimNT.fa) into the `database` directory.
3. Move the `taxonomy.db` file into the `database` directory.

### MakeBlastDB Command
If you have not already done so, please perform the `makeblastdb` command to your database file (e.g., slimNT.fa). This step was done in the [blast_database.md README directions](https://github.com/GW-HIVE/CensuScope/blob/readme-updates-crw/docs/blast_database.md).

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

### Docker Command Line Options

```shell
usage: censuscope [options]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -i ITERATIONS, --iterations ITERATIONS
                        The number of sample iterations to perform
  -s SAMPLE_SIZE, --sample-size SAMPLE_SIZE
                        The number of reads to sample for each iteration
  -t TAX_DEPTH, --tax-depth TAX_DEPTH
                        The taxonomy depth to report in the final results
  -q QUERY_PATH, --query_path QUERY_PATH
                        Input file name
  -d DATABASE, --database DATABASE
                        BLAST database name
```
<br>

## Building CensuScope via Docker

A docker file is provided to allow easy building of the CensuScope container. Once all of your files are in their respective directories it can be run at the root directory `CensuScope` (or where the Dockerfile is found).

Run the command:

```
docker build -t  censuscope:tag .
```

- `:tag` It is suggested to add a docker tag which allows for multiple docker images to be created without overwriting.
- Suggestions: censuscope:version (`censuscope:v1.0`), censuscope:initials (`censuscope:ABC`), etc.

This will build a container named `censuscope:tag`. This name will be in input for the `docker run` command below.


## Running the container via Docker

The CensuScope container can be run via docker on the command line in Linux/Windows by running (replace paths and input file name as necessary; if you followed the steps above, only the "BLASTDB" needs to be updated):

```shell
docker run -v /PATH/TO/DATABASE_FOLDER:/app/blastdb \
  -v ~/CensuScope/inputs:/app/inputs \
  -v ~/CensuScope/temp_dirs:/app/temp_dirs  \
  censuscope:tag \
  python lib/censuscope.py \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/QUERY.FILE \
  --database /app/blastdb/<BLASTDB FILE>
```
- `/PATH/TO/DATABASE_FOLDER` should point to the filepath directory that contains both taxonomy.db and your database file.
- `censuscope:tag` should be the name of the docker image you created in the previous step.
- `--query_path /app/inputs/QUERY.FILE` change the `QUERY.FILE` to the name of your sample file found in the `inputs/` directory you created.
- `--database /app/blastdb/<BLASTDB FILE>` change the `<BLASTDB FILE>` to the name of your database file. You may need to update the filepath to include the directory created by the `makeblastdb` command. See example below.

More Specific Example:
```shell
docker run -v /home/desktop/CenuScope/database:/app/blastdb \
  -v /home/desktop/CensuScope/inputs:/app/inputs \
  -v /home/desktop/CensuScope/temp_dirs:/app/temp_dirs  \
  censuscope:v1.1 \
  python lib/censuscope.py \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/c.sebaeus_R1.fasta \
  --database /app/blastdb/slimNT/slimNT.fa
```


See [Running via the command line](#running-via-the-command-line) above for a breakdown of the command line flags. 

Running this command will create a date-time named folder at the specified location `/path/to/CensuScope/temp_dirs` with all the intermediate and result files. 

## Results
Once you have run the CensuScope Docker, the results and outputs will be in `/temp_dirs/` in your `CensuScope` directory. 

To pull from the GitHub Container Registry us the following:

    docker pull ghcr.io/gw-hive/censuscope:2.0.1
