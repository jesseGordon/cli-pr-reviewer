# Makefile for installing the PR Review CLI tool

CLI_NAME = pr-review
SCRIPT_PATH = $(PWD)/cli-reviewer.py
INSTALL_PATH = /usr/local/bin/$(CLI_NAME)

.PHONY: install uninstall reinstall binary pip-install pipx-install clean dist setup-dev setup-binary setup-pipx

# Direct installation (traditional symlink, legacy method)
install:
	@echo "Installing $(CLI_NAME) via symlink..."
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
	pip install -e .

# Install from source with pipx (isolated environment)
pipx-install:
	@echo "Installing with pipx (isolated environment)..."
	pipx install --editable --force .

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

# Set up development environment
setup-dev: clean
	@echo "Setting up development environment..."
	pip install -e ".[dev]"
	@echo "Development setup complete."

# Set up binary installation
setup-binary: clean binary
	@echo "Installing binary to PATH..."
	mkdir -p $(HOME)/bin
	cp dist/$(CLI_NAME) $(HOME)/bin/
	@echo "Binary installed to ~/bin/$(CLI_NAME)"
	@echo "Ensure ~/bin is in your PATH."

# Set up pipx installation (recommended for users)
setup-pipx: clean
	@echo "Installing with pipx (isolated environment)..."
	pipx install .

