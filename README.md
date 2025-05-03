# PR Review CLI

An AI-powered command-line tool for reviewing pull requests and code changes using various AI providers.

## Features

- 🧠 **AI-Powered Code Reviews**: Get detailed feedback on your code changes
- 🚀 **Multiple AI Providers**: Support for Gemini, OpenAI, and Anthropic (coming soon)
- 🌈 **Rich Terminal Output**: Beautifully formatted markdown in your terminal
- ⚙️ **Flexible Configuration**: Configure via CLI, environment variables, or config file
- 🔄 **Git Integration**: Works directly with your Git diffs
- 📝 **Multiple Diff Sources**: Review staged, unstaged, specific files, or commit ranges
- 💻 **Syntax Highlighting**: Colorized diffs for better readability
- 📊 **Diff Truncation**: Limit large diffs to avoid token limits
- 📦 **Standalone Binary**: Single-file executable without Python dependency

## Installation

There are several ways to install the PR Review CLI tool:

### Option 1: Pip Installation (Recommended for most users)

```bash
# Install directly from PyPI (once published)
pip install pr-review

# Or install from the repository
git clone https://github.com/your-username/cli-pr-reviewer.git
cd cli-pr-reviewer
pip install .
```

### Option 2: Pipx Installation (Isolated environment)

```bash
# Install in an isolated environment (recommended)
pipx install pr-review

# Or install from the repository
git clone https://github.com/your-username/cli-pr-reviewer.git
cd cli-pr-reviewer
pipx install .
```

### Option 3: From Source

```bash
# Clone the repository
git clone https://github.com/your-username/cli-pr-reviewer.git
cd cli-pr-reviewer

# Install dependencies
pip install -r requirements.txt

# Make the script executable and add to your PATH
chmod +x cli-reviewer.py
ln -s $(pwd)/cli-reviewer.py /usr/local/bin/pr-review

# Or use the Makefile
make install
```

### Option 4: Standalone Binary

```bash
# Build the standalone executable
make binary
# or
python build_executable.py

# Install the executable
sudo cp dist/pr-review /usr/local/bin/
# or
cp dist/pr-review ~/bin/
```

## Requirements

- Python 3.8+ (not needed for standalone binary)
- Git
- API keys for at least one of the supported AI providers

## Configuration

The tool uses a configuration hierarchy:

1. Command-line arguments
2. Environment variables
3. Configuration file (~/.pr-review.toml)
4. Default values

### Setting up your API keys

```bash
# Via environment variables
export GEMINI_API_KEY=your_api_key
export OPENAI_API_KEY=your_api_key
export ANTHROPIC_API_KEY=your_api_key

# Or via config command
pr-review config set api_keys.gemini your_api_key
pr-review config set api_keys.openai your_api_key
pr-review config set api_keys.anthropic your_api_key
```

## Usage

### Reviewing Code Changes

```bash
# Review staged changes (default)
pr-review review

# Review unstaged changes
pr-review review --unstaged

# Review specific file
pr-review review --file path/to/file.js

# Review specific commit
pr-review review --commit abc123

# Review commit range
pr-review review --commit HEAD~3..HEAD

# Limit diff size
pr-review review --max-chars 5000

# Use a different AI provider
pr-review review --provider openai

# Specify a different model
pr-review review --model gpt-4
```

### Viewing Diffs with Syntax Highlighting

```bash
# Show staged changes with syntax highlighting
pr-review diff

# Show unstaged changes
pr-review diff --unstaged

# Show specific file
pr-review diff --file path/to/file.js

# Show specific commit
pr-review diff --commit abc123

# Show commit range
pr-review diff --commit HEAD~3..HEAD

# Disable syntax highlighting
pr-review diff --no-color
```

### Managing Configuration

```bash
# List all configuration values
pr-review config list

# Get a specific config value
pr-review config get provider

# Set a configuration value
pr-review config set provider openai

# Remove a configuration value
pr-review config unset custom_setting
```

### Shell Completion

```bash
# For Bash
pr-review completion bash > ~/.pr-review-completion.bash
echo 'source ~/.pr-review-completion.bash' >> ~/.bashrc

# For Zsh
pr-review completion zsh > ~/.zfunc/_pr-review
echo 'fpath+=~/.zfunc' >> ~/.zshrc

# For Fish
pr-review completion fish > ~/.config/fish/completions/pr-review.fish
```

## Advanced Options

### Diff Truncation

For large diffs, you can limit the size to avoid token limits in the AI models:

```bash
pr-review review --max-chars 10000
```

This will truncate the diff to 10,000 characters before sending to the AI service.

### Syntax Highlighting

The `diff` command uses syntax highlighting to make diffs more readable:

```bash
pr-review diff
```

You can disable this with the `--no-color` flag:

```bash
pr-review diff --no-color
```

## License

MIT 