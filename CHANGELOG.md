# Changelog

## v2.0.0 (Unreleased)

### Architecture & Code Structure
- Completely refactored code into proper Python package structure
- Modularized code with separate modules for different functionality
- Improved error handling throughout the codebase
- Removed dependency on rich-click in favor of custom formatting
- Added proper typing and docstrings

### Features
- Added improved syntax highlighting with Pygments
- Support for multiple AI providers (Gemini, OpenAI, Anthropic)
- Added diff truncation to handle large diffs
- Advanced diff sources (staged, unstaged, commit ranges)

### Packaging & Installation
- Added standalone binary distribution using PyInstaller
- Made package properly pip-installable with entry points
- Added support for isolated installation with pipx
- Enhanced Makefile with separate targets for development, binary, and pip installation
- Added backwards-compatibility wrapper for traditional installation

## v1.0.0 (Initial Release)

### Features
- Basic PR review capabilities using Gemini AI
- Git integration for reviewing code changes
- Configuration management via CLI and config file
- Rich terminal output with markdown formatting 