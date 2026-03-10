#!/bin/bash

set -e

./lib/nucleotide-db.sh CensuScopeDB/ taxonomy.db
./lib/add-nodes.sh CensuScopeDB/nodes.dmp taxonomy.db
./lib/add-names.sh CensuScopeDB/names.dmp taxonomy.db
cp taxonomy.db temp.db
./lib/add-hosts.sh CensuScopeDB/host.dmp temp.db
mv temp.db taxonomy.db
