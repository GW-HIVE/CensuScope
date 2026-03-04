# Documentation on Deployment and Files
This directory contains documentation related to the deployment and supporting resources for running CensuScope in a Docker environment. Because several components are required to configure and execute CensuScope (such as reference databases, configuration files, and infrastructure dependencies), the documentation is organized into multiple files, each describing a specific component of the system.

This README serves as an overview and table of contents for the documentation in this folder. Each linked document explains a specific resource, how it is structured, how it is generated or obtained, and how it is used within the CensuScope workflow.

## Taxonomdy.db Documentation
This document, [taxonomy.md](https://github.com/GW-HIVE/CensuScope/edit/christie-readmes/docs/taxonomy.md), describes the taxonomy database used by CensuScope: its purpose, schema, build process, and validation. The taxonomy database is treated as static reference infrastructure and is not modified during execution. The taxonomy.db is a required file to run the Censuscope. 
- The taxonomy.md README goes into detail about what is contained within the database file, how to retreive it, and how it is used in the Censuscope steps. 
