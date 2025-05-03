# Makefile for installing the PR Review CLI tool

CLI_NAME = git-pr-review
SCRIPT_PATH = $(PWD)/cli-reviewer.py
INSTALL_PATH = /usr/local/bin/$(CLI_NAME)

.PHONY: install uninstall reinstall binary pip-install pipx-install clean dist

# Traditional symlink installation
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

# Build standalone binary
binary:
	@echo "Building standalone binary..."
	python build_executable.py

# Install from source with pip
pip-install:
	@echo "Installing with pip..."
	pip install .

# Install from source with pipx (isolated environment)
pipx-install:
	@echo "Installing with pipx (isolated environment)..."
	pipx install .

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/ *.spec
	@echo "Cleaned."

# Build distribution packages
dist: clean
	@echo "Building distribution packages..."
	python -m pip install --upgrade pip build twine
	python -m build
	@echo "Built distribution packages. Use 'twine upload dist/*' to upload to PyPI."

# All-in-one setup: builds binary and installs with pipx
setup: clean binary pipx-install

