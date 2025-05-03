# Changelog

## v2.0.0 (2024)

### Major Changes
- Completely refactored CLI using Click and Rich libraries
- Added proper subcommands: `review`, `diff`, `config`, `completion`
- Added configuration management with hierarchical config system
- Added support for multiple AI providers (Gemini, OpenAI, Anthropic)
- Added rich terminal output with markdown rendering
- Added proper error handling and user-friendly error messages
- Added command suggestion for unknown commands
- Added shell completion support for Bash, Zsh, and Fish

### New Features
- **Config Management**: Added `config` subcommand with `list`, `get`, `set`, and `unset` operations
- **Provider Selection**: Support for choosing different AI providers via config or CLI flags
- **Shell Completion**: Added autocomplete scripts for various shells
- **Better UX**: Improved progress indicators, error messages, and help text
- **Diff Preview**: Added `diff` subcommand to preview what will be sent for review

### Other Improvements
- Added proper type annotations throughout the codebase
- Better exception handling with custom error classes
- More informative error messages with appropriate exit codes
- Comprehensive documentation in README.md

## v1.0.0 (Initial Release)

- Basic PR review functionality using Gemini API
- Simple spinner for progress indication
- Git diff integration
- Optional Markdown rendering with 'bat' if available 