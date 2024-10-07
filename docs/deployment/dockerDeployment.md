# CensuScope Docker Deployment
## Contents
- [Requirements](#requirements)
- [Running via the cmooand line](#running-via-the-cmooand-line)
- [Building CensuScope via Docker](#building-censuscope-via-docker)
- [Running the container via Docker](#running-the-container-via-docker)
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

The build process will copy the main script and the test data into the container. If no database is present one will be created and the test data will be loaded (taken from `config/fixtures/local_data.json`).

### Running the container via Docker

The BCO Api container can be run via docker on the command line in Linux/Windows by running:

`docker run --rm --network host -it bco_api:latest`

The BCO Api container can be run via docker on the command line in MacOS by running:

`docker run --rm -p 8000:8000 -it bco_api:latest`

This will expose the server at `http://127.0.0.1:8000`, whitch is where all of the default settings will expect to find the BCODB. 

#### Overriding the port

It is possible to override the port 8000 to whatever port is desired.  This is done by running the container with 8080 representing the desired port.

`docker run --rm --network host -it bco_api:latest 0.0.0.0:8080`


NOTE: The ip address of 0.0.0.0 is to allow the web serer to properly associate with 127.0.0.1 - if given 127.0.0.1 it will not allow communications outside of the container!

You can also give it a specific network created with `docker network create` if you wanted to give assigned IP addresses.
