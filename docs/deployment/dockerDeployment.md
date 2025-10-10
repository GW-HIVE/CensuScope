# CensuScope Docker Deployment
## Contents
- [Requirements](#requirements)
- [Running via the command line](#running-via-the-command-line)
- [Building CensuScope via Docker](#building-censuscope-via-docker)
- [Running the container via Docker](#running-the-container-via-docker)
- [Pushing a new build to GitHub](#pushing-a-new-build-to-github)
- [Pulling a Container from GitHub](#Pulling-a-container-from-github)
### Requirements
1. Python 3: [3.10.6 reccomended](https://www.python.org/downloads/release/python-3106/) (for command line use or development)
2. [Docker](https://docs.docker.com/engine/install/)
    - Links if using Docker Desktop:
      - [Docker Desktop for Linux](https://docs.docker.com/desktop/install/linux-install/)
      - [Docker Desktop for Mac (macOS)](https://docs.docker.com/desktop/install/mac-install/)
      - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
3. An indexed database and optional taxonomy map (recommend doing this in your home directory or somewhere you have full permissions)
    - Use `makeblastdb` to build a database
      - [Install instructions](https://www.ncbi.nlm.nih.gov/books/NBK52640/)
      - Databses:
        - [NCBI's NT databases](https://www.ncbi.nlm.nih.gov/books/NBK52640/)
        - [slimNT database](https://hive.biochemistry.gwu.edu/static/slimNT.fa.gz) (21.1GB)
        - [slimNT taxonomy](https://hive.biochemistry.gwu.edu/static/slimNT.db.gz) (16.8GB)
    - Note that if you build an NCBI taxonomy database that you may have to rename columns, as the script is expecting `taxid` (not `tax_id`) and `name`(not `name_txt`).
        - E.g. `sqlite3 taxonomy.db "ALTER TABLE names RENAME COLUMN name_txt TO name;"`
<br>
Note: Downloading the files and building the database may take a lot of time. Plan ahead.

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
### Build project folders
```
mkdir -p {inputs,temp_dirs}
chmod 777 temp_dirs
```
Move your query file into this directory and name appropriately (the command calls `QUERY.FILE`).

### Command line options

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

## Building CensuScope via Docker

A docker file is provided to allow easy building of the CensuScope container.  This can be done from the root directory (the directory with Dockerfile in it) by running:

`docker build -t  censuscope .`

This will build a container named `censuscope`.

The build process will copy the main script into the container.


## Running the container via Docker

The CensuScope container can be run via docker on the command line in Linux/Windows by running (replace paths and input file name as necessary; if you followed the steps above, only the "BLASTDB" needs to be updated):

```shell
docker run -v /PATH/TO/BLASTDBFILE:/app/blastdb \
  -v ~/CensuScope/inputs:/app/inputs \
  -v ~/CensuScope/temp_dirs:/app/temp_dirs  \
  censuscope \
  python lib/censuscope.py \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth species \
  --query_path /app/inputs/QUERY.FILE \
  --database /app/blastdb/<BLASTDB FILE>
```

See [Running via the command line](#running-via-the-command-line) above for a breakdown of the parameters. 

This will create a date-time named folder at the specified location `/path/to/temp_dirs` with all the intermediate and result files. 

## Pushing a new build to GitHub
Publishing to GitHub requires a Public Access Token (PAT). See the [GitHub Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) for more information.

The preferred method is to add your PAT to a `bashrc` or equivalent file. 
    
    export CR_PAT=YOUR_TOKEN

This will allow you to run the following command to log in:

    $ echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
    > Login Succeeded

The container needs to be tagged using the following format:`docker tag <imageId or imageName> <hostname>:<repository-port>/<image>:<tag>`

So for our container it woul be:

    docker tag censuscope ghcr.io/gw-hive/censuscope:2.0.1

And then you can push using this format:`docker push <hostname>:<repository-port>/<image>:<tag>`

So for this container it would be:

    docker push ghcr.io/gw-hive/censuscope:2.0.1

## Pulling a Container from GitHub

To pull from the GitHub Container Registry us the following:

    docker pull ghcr.io/gw-hive/censuscope:2.0.1
