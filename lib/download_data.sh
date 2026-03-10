#!/bin/bash

set -e

pushd .. 2>&1 > /dev/null

curl -o CensuScopeDB/nucl_gb.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz
curl -o CensuScopeDB/nucl_wgs.accession2taxid.EXTRA.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.EXTRA.gz
curl -o CensuScopeDB/nucl_wgs.accession2taxid.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/accession2taxid/nucl_wgs.accession2taxid.gz
curl -o CensuScopeDB/new_taxdump.tar.gz \
    ftp://ftp.ncbi.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz 


popd