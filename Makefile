# Makefile for installing the CLI tool

CLI_NAME = git-pr-review
SCRIPT_PATH = $(PWD)/cli-reviewer.py
INSTALL_PATH = /usr/local/bin/$(CLI_NAME)

.PHONY: install uninstall reinstall

install:
	@echo "Installing $(CLI_NAME)..."
	@sudo ln -sf $(SCRIPT_PATH) $(INSTALL_PATH)
	@sudo chmod +x $(INSTALL_PATH)
	@echo "$(CLI_NAME) installed successfully."

uninstall:
	@echo "Removing $(CLI_NAME)..."
	@sudo rm -f $(INSTALL_PATH)
	@echo "$(CLI_NAME) removed."

reinstall: uninstall install

