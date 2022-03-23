.POSIX:

PREFIX = ~/.local/bin
CONFIG = ~/.config/pirtuk

CURRENT_DIR = $(shell pwd)

install: $(PREFIX)
	if [ ! -d $(CONFIG) ]; then mkdir -p $(CONFIG); fi
	echo "#!/bin/bash" > pirtuk.sh
	echo python3 $(CURRENT_DIR)/pirtuk.py '"$$@"' >> pirtuk.sh
	chmod +x pirtuk.sh 
	ln -s $(CURRENT_DIR)/pirtuk.sh $(PREFIX)/pirtuk 

uninstall: 
	rm -r $(PREFIX)/pirtuk 
	rm pirtuk.sh

.PHONY: install uninstall
