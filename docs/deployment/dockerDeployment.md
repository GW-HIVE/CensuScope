# CensuScope Docker Deployment


### Requirements
- Python 3: [3.10.6 reccomended](https://www.python.org/downloads/release/python-3106/)
- Docker:
    - [Docker Desktop for Linux](https://docs.docker.com/desktop/install/linux-install/)
    - [Docker Desktop for Mac (macOS)](https://docs.docker.com/desktop/install/mac-install/)
    - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

## Clone the repository
```
git clone https://github.com/GW-HIVE/CensuScope/
```

## Enter the repository
```
cd CensuScope
```

**Make sure you are on the desired branch (Check for latest branch):**

```
git switch [DESIRED BRANCH TAG]
```

### Building CensuScope via Docker

A docker file is provided to allow easy building of the BCO API.  This can be done from the root directory (the directory with Dockerfile in it) by running:

`docker build -t  censuscope .`

This will build a container named `censuscope`.

The build process (via the `entrypoint.sh` script) will check for an existing database in the repository and run migrations. If no database is present one will be created and the test data will be loaded (taken from `config/fixtures/local_data.json`).

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
