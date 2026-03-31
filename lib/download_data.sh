#!/bin/bash

set -e
# This script downloads the 4 zip files needes to build the Taxonomy.db file. These files are updated monthly by NCBI so update the files as you see fit.
# This script only needs to be ran once and not run every time the docker needs to be built.
# Note: This download will take anywhere between 15 - 60 mins.

pushd .. 2>&1 > /dev/null

curl -o CensuScopeDB/nucl_gb.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz
curl -o CensuScopeDB/nucl_wgs.accession2taxid.EXTRA.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.EXTRA.gz
curl -o CensuScopeDB/nucl_wgs.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz
curl -o CensuScopeDB/new_taxdump.tar.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz 

popd 2>&1 > /dev/null
