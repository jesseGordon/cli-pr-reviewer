# Changelog

## v2.0.0 (Unreleased)

### Features
- Added improved syntax highlighting with Pygments
- Support for multiple AI providers (Gemini, OpenAI, Anthropic)
- Added diff truncation to handle large diffs
- Advanced diff sources (staged, unstaged, commit ranges)

### Packaging & Installation
- Added standalone binary distribution using PyInstaller
- Made package pip-installable with proper entry points
- Added support for isolated installation with pipx
- Enhanced Makefile with targets for different installation methods

## v1.0.0 (Initial Release)

### Features
- Basic PR review capabilities using Gemini AI
- Git integration for reviewing code changes
- Configuration management via CLI and config file
- Rich terminal output with markdown formatting 