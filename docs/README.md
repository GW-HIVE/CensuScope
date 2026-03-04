# Documentation on Deployment and Files
This directory contains documentation related to the deployment and supporting resources for running CensuScope in a Docker environment. Because several components are required to configure and execute CensuScope (such as reference databases, configuration files, and infrastructure dependencies), the documentation is organized into multiple files, each describing a specific component of the system.

This README serves as an _overview_ and _table of contents_ for the documentation in this folder. Each linked document explains a specific resource, how it is structured, how it is generated or obtained, and how it is used within the CensuScope workflow.

## Taxonomdy Database Documentation
This document, [taxonomy.md](https://github.com/GW-HIVE/CensuScope/edit/christie-readmes/docs/taxonomy.md), describes the taxonomy database used by CensuScope: its purpose, schema, build process, and validation. The taxonomy database is treated as static reference infrastructure and is not modified during execution. The taxonomy.db is a required file to run the Censuscope. 
- The taxonomy.md README goes into detail about what is contained within the database file, how to retreive it, and how it is used in the Censuscope steps.

## Docker Deployment Guide (Primary)
This document, [dockerDeployment.md](https://github.com/GW-HIVE/CensuScope/blob/christie-readmes/docs/deployment/dockerDeployment.md), provides the primary guide for deploying and running CensuScope using Docker.

- The document outlines the software and data requirements needed to run CensuScope, including Python, Docker, and an indexed BLAST database.
- It explains how to clone the repository, prepare the required project directories, and run CensuScope directly from the command line.
- Detailed instructions are provided for building the CensuScope Docker image and executing the container with mounted input, database, and output directories.
- The guide also includes instructions for publishing container images to the GitHub Container Registry (GHCR) and pulling existing container builds.
- Additional notes describe database preparation, taxonomy database expectations, and configuration considerations when running the workflow.

## Local CLI Deployment
This document, [localDeployment.md](https://github.com/GW-HIVE/CensuScope/blob/christie-readmes/docs/deployment/localDeployment.md), describes how to run CensuScope locally from the command line without using Docker.

- The guide explains how to install required dependencies such as Python, BLAST+, SQLite, and standard UNIX tools.
- It provides instructions for building a nucleotide BLAST database from reference FASTA files.
- The document walks through constructing the reduced taxonomy database from the NCBI taxonomy dump.
- Example commands are provided for running CensuScope via the CLI with configurable parameters such as iterations, sample size, and thread count.
- Additional sections describe expected output files, performance considerations, and troubleshooting common issues related to BLAST or taxonomy database configuration.
  
## Docker Compose Deployment
This document, [docker_compose.md](https://github.com/GW-HIVE/CensuScope/blob/christie-readmes/docs/deployment/docker_compose.md), provides step-by-step instructions for running CensuScope using Docker Compose and the official `ghcr.io/gw-hive/censuscope` container image.

- The guide outlines the prerequisites required to run the container, including Docker Desktop, Docker Compose, and locally available FASTQ and BLAST database files.
- It provides an example project directory structure and a sample `docker-compose.yml` configuration for launching CensuScope.
- The document explains how to mount local data directories into the container, configure runtime parameters, and execute the workflow.
- Additional sections describe how output files are written to the `temp_dirs` directory, how to stop and remove containers, and troubleshooting steps for common issues such as Docker file-mount permissions on macOS.
