TAXONOMY_DIR := raw_data/
NUC = taxonomy.db

usage:
	@echo -e "Usage:\n'make_taxonomy_db.sh nucleotide' will create a nucleotide taxonomy db"
	@echo -e "'make_taxonomy_db.sh vacuum' will clean up thre DB."
	@echo -e "'make_taxonomy_db.sh clean' will remove thre DB. \n"

all: clean nucleotide

vacuum:
	./vaccum.sh $(NUC)

# $(DB): clean taxids nodes names hosts

nucleotide:
	echo $(TAXONOMY_DIR) $(NUC)
	rm -f $(NUC)
	./lib/nucleotide-db.sh $(TAXONOMY_DIR)accession2taxid/ $(NUC)
	./lib/add-nodes.sh $(TAXONOMY_DIR)new_taxdump/nodes.dmp $(NUC)
	./lib/add-names.sh $(TAXONOMY_DIR)new_taxdump/names.dmp $(NUC)
	./lib/add-hosts.sh $(TAXONOMY_DIR)new_taxdump/host.dmp $(NUC)

clean:
	rm -f $(NUC)
