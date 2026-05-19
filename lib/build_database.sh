#!/bin/bash

set -e

pushd .. 2>&1 > /dev/null
# nodes, names, and host are all inside new_taxdump.tar.gz. If it is not uncompressed then this code will fail.
# Note the filepath of nodes, names, and host. 
if [ ! -f CensuScopeDB/nodes.dmp ] || [ ! -f CensuScopeDB/names.dmp ] || [ ! -f CensuScopeDB/host.dmp ]; then
    tar -xzf CensuScopeDB/new_taxdump.tar.gz -C CensuScopeDB nodes.dmp names.dmp host.dmp
fi

echo "Start building database: $(date)"
./lib/nucleotide-db.sh CensuScopeDB/ taxonomy.db

./lib/add-nodes.sh CensuScopeDB/nodes.dmp taxonomy.db

./lib/add-names.sh CensuScopeDB/names.dmp taxonomy.db

cp taxonomy.db temp.db
./lib/add-hosts.sh CensuScopeDB/host.dmp temp.db

mv temp.db taxonomy.db

echo "Finished building database: $(date)"

popd 2>&1 > /dev/null
