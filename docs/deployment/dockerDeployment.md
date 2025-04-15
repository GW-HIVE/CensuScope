# CensuScope Docker Deployment
## Contents
- [Requirements](#requirements)
- [Running via the command line](#running-via-the-command-line)
- [Building CensuScope via Docker](#building-censuscope-via-docker)
- [Running the container via Docker](#running-the-container-via-docker)
- [Pushing a new build to GitHub](#pushing-a-new-build-to-github)
- [Pulling a Container from GitHub](#Pulling-a-container-from-github)
### Requirements
- Python 3: [3.10.6 reccomended](https://www.python.org/downloads/release/python-3106/) (for command line use or development)
- Docker:
    - [Docker Desktop for Linux](https://docs.docker.com/desktop/install/linux-install/)
    - [Docker Desktop for Mac (macOS)](https://docs.docker.com/desktop/install/mac-install/)
    - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

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

The CensuScope container can be run via docker on the command line in Linux/Windows by running:

```shell
docker run -v /path/to/blastdb:/app/blastdb \
  -v /path/to/query/files:/app/inputs \
  -v /path/to/temp_dirs:/app/temp_dirs  \
  censuscope \
  python lib/censuscope.py \
  --iterations 5 \
  --sample-size 10 \
  --tax-depth 5 \
  --query_path /app/inputs/QUERY.FILE \
  --database /app/blastdb/FOLDER/BLASTDB
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