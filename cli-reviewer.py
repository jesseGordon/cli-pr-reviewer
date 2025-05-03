#!/usr/bin/env python3

import os
import sys
import subprocess
import textwrap
import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from difflib import get_close_matches

import click
import google.generativeai as genai
import tomli
import tomli_w
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Global constants
DEFAULT_CONFIG = {
    "provider": "gemini",
    "model": "gemini-2.5-flash-preview-04-17",
    "api_keys": {
        "gemini": "",
        "openai": "",
        "anthropic": ""
    }
}

CONFIG_PATH = Path.home() / ".pr-review.toml"
console = Console()


# Enable command suggestion for the CLI
class SuggestionGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            # Wrap command to use our custom help formatter
            original_format_help = rv.format_help
            rv.format_help = lambda ctx, formatter: self.format_subcommand_help(original_format_help, ctx, formatter)
            return rv
        
        matches = get_close_matches(cmd_name, self.list_commands(ctx), n=3, cutoff=0.6)
        if matches:
            # Show error and suggestions with boxes
            suggestion_text = f"Unknown command '{cmd_name}'.\n\nDid you mean one of these?\n"
            suggestion_text += "\n".join(f"  {match}" for match in matches)
            suggestion_text += "\n\nRun 'pr-review --help' to see all available commands."
            console.print(Panel(suggestion_text, title="Error", border_style="red", box=ROUNDED))
            ctx.exit(2)
        else:
            console.print(Panel(f"Unknown command '{cmd_name}'.", title="Error", border_style="red", box=ROUNDED))
            ctx.exit(2)
        return None

    def format_help(self, ctx, formatter):
        # Override to add our own help formatting
        super().format_help(ctx, formatter)
        self._display_formatted_help(formatter.getvalue())
        ctx.exit()

    def format_subcommand_help(self, original_format_help, ctx, formatter):
        # Call the original format_help to get the help text
        original_format_help(ctx, formatter)
        self._display_formatted_help(formatter.getvalue())
        ctx.exit()

    def _display_formatted_help(self, help_text):
        # Extract sections
        sections = help_text.split("\n\n")
        usage = sections[0] if len(sections) > 0 else ""
        
        # Get description (may be multiple paragraphs)
        description_sections = []
        description_start = 1
        for i in range(1, len(sections)):
            if sections[i].startswith("Options:") or sections[i].startswith("Commands:"):
                break
            description_sections.append(sections[i])
            description_start += 1
        
        description = "\n\n".join(description_sections) if description_sections else ""
        
        # Create formatted help with boxes
        console.print(usage)
        if description:
            console.print(description)
        
        # Extract and format options and commands
        options_content = []
        commands_content = []
        
        in_options = False
        in_commands = False
        
        for line in help_text.split("\n"):
            line = line.strip()
            if line == "Options:":
                in_options = True
                in_commands = False
                continue
            elif line == "Commands:":
                in_options = False
                in_commands = True
                continue
            elif not line:
                continue  # Skip empty lines
            
            if in_options and line and not line.startswith("Options:"):
                option_parts = line.split("  ", 1)
                if len(option_parts) == 2:
                    # Pad option name to a fixed width
                    option = option_parts[0].strip().ljust(18)
                    options_content.append(f"[cyan]{option}[/] {option_parts[1].strip()}")
            
            if in_commands and line and not line.startswith("Commands:"):
                cmd_parts = line.split("  ", 1)
                if len(cmd_parts) == 2:
                    # Pad command name to a fixed width
                    command = cmd_parts[0].strip().ljust(18)
                    commands_content.append(f"[green]{command}[/] {cmd_parts[1].strip()}")
        
        # Display sections with borders
        if options_content:
            options_text = "\n".join(options_content)
            console.print(Panel(options_text, title="Options", border_style="blue", box=ROUNDED))
        
        if commands_content:
            commands_text = "\n".join(commands_content)
            console.print(Panel(commands_text, title="Commands", border_style="blue", box=ROUNDED))


class PrReviewError(Exception):
    """Base exception for PR Review errors with exit code support"""
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


def load_config() -> Dict[str, Any]:
    """Load configuration from file or create default if not exists"""
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomli.load(f)
    except Exception as e:
        raise PrReviewError(f"Error loading config: {e}", exit_code=2)


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file"""
    try:
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(config, f)
    except Exception as e:
        raise PrReviewError(f"Error saving config: {e}", exit_code=2)


def get_git_diff(diff_args: List[str]) -> str:
    """
    Return the output of `git diff` with the given arguments.
    If no arguments are provided, defaults to staged changes.
    """
    cmd = ["git", "diff"] + diff_args if diff_args else ["git", "diff", "--cached"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise PrReviewError(f"Git error: {e.stderr.strip()}", exit_code=3)


def make_prompt(diff_text: str) -> str:
    """
    Construct the prompt for the AI API in Markdown.
    """
    header = textwrap.dedent("""
    You're an expert software engineer performing a detailed code review.
    Evaluate the provided pull request (PR) carefully, considering correctness,
    readability, efficiency, adherence to best practices, and potential edge cases
    or bugs. Provide constructive feedback highlighting specific issues or suggestions
    for improvements. Conclude your review explicitly with either `APPROVED` if the PR
    meets high standards and can be merged without further changes, or `MAKE CHANGES`
    if revisions are required, clearly stating your reasoning.

    **Format in MARKDOWN syntax.** Do not wrap your entire response in markdown code fences (like ```markdown ... ```); just provide the raw markdown content starting directly with your feedback or conclusion.
                                 
    Example:

    ```
    ## Title: [Give a title for the PR]
    Feedback:
    - [Specific issue or suggestion #1]
    - [Specific issue or suggestion #2]
    - [Further detailed feedback as needed]
                             
    Commit message:
    - [Commit message]

    Conclusion: APPROVED

    or

    ```
    ## Title: [Give a title for the PR]
    Feedback:
    - [Specific issue or suggestion #1]
    - [Specific issue or suggestion #2]
    - [Further detailed feedback as needed]
                             
    Conclusion: MAKE CHANGES
    """)
    return header + diff_text


def send_to_gemini(prompt: str, api_key: str, model: str) -> Any:
    """Send the prompt to the Gemini API and return the response stream iterator."""
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    return model_obj.generate_content(prompt, stream=True)


def send_to_provider(prompt: str, provider: str, model: str, api_key: str) -> Any:
    """Send prompt to the selected AI provider and return response stream"""
    if provider == "gemini":
        return send_to_gemini(prompt, api_key, model)
    elif provider == "openai":
        # Placeholder for OpenAI implementation
        raise PrReviewError("OpenAI provider not yet implemented", exit_code=4)
    elif provider == "anthropic":
        # Placeholder for Anthropic implementation
        raise PrReviewError("Anthropic provider not yet implemented", exit_code=4)
    else:
        raise PrReviewError(f"Unknown provider: {provider}", exit_code=4)


def print_response(response_stream: Any) -> None:
    """Print the formatted response from the AI provider"""
    # Collect the entire response
    full_text = ""
    for chunk in response_stream:
        if hasattr(chunk, "text"):
            full_text += chunk.text
    
    # Render markdown with Rich
    md = Markdown(full_text)
    console.print(Panel(md, title="AI PR Review", border_style="green", box=ROUNDED))


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, cls=SuggestionGroup)
@click.version_option(version="2.0.0")
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    PR Review CLI - Generate AI-powered code reviews for your pull requests.
    
    Examples:
      pr-review review                  # Review staged changes
      pr-review review HEAD~3..HEAD     # Review last 3 commits
      pr-review config set provider openai  # Change the AI provider
    """
    # Initialize context object for sharing data between commands
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    try:
        # Load configuration
        ctx.obj['config'] = load_config()
    except PrReviewError as e:
        console.print(Panel(f"Error: {e.message}", title="Error", border_style="red", box=ROUNDED))
        if verbose:
            console.print_exception()
        sys.exit(e.exit_code)


@cli.command('review', short_help="Review code changes")
@click.argument('diff_args', nargs=-1)
@click.option('--provider', help="AI provider to use [gemini|openai|anthropic]")
@click.option('--model', help="Specific model to use")
@click.pass_context
def review_command(ctx: click.Context, diff_args: List[str], provider: Optional[str], model: Optional[str]) -> None:
    """
    Review code changes using AI.
    
    DIFF_ARGS are passed directly to 'git diff'. If not provided, 
    staged changes (--cached) will be reviewed.
    
    Examples:
      pr-review review                  # Review staged changes
      pr-review review HEAD~3..HEAD     # Review last 3 commits
    """
    try:
        config = ctx.obj['config']
        
        # Override config with command line options if provided
        active_provider = provider or config.get('provider', 'gemini')
        active_model = model or config.get('model', 'gemini-2.5-flash-preview-04-17')
        
        # Get API key for the selected provider
        api_key = os.environ.get(f"{active_provider.upper()}_API_KEY") or config.get('api_keys', {}).get(active_provider, '')
        
        if not api_key:
            error_msg = (f"{active_provider.upper()}_API_KEY not found in environment or config. "
                        f"Set it with 'pr-review config set api_keys.{active_provider} YOUR_KEY' or "
                        f"export {active_provider.upper()}_API_KEY=your_key")
            console.print(Panel(error_msg, title="API Key Error", border_style="red", box=ROUNDED))
            sys.exit(1)
        
        # Get the git diff
        diff_text = get_git_diff(list(diff_args))
        if not diff_text.strip():
            console.print(Panel("No changes found.", title="Information", border_style="yellow", box=ROUNDED))
            return
        
        # Create the prompt
        prompt = make_prompt(diff_text)
        
        # Show progress while waiting for response
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Getting PR review..."),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Waiting...", total=None)
            # Send to AI provider and get response
            review_stream = send_to_provider(prompt, active_provider, active_model, api_key)
            
        # Print the review
        print_response(review_stream)
        
    except PrReviewError as e:
        console.print(Panel(f"Error: {e.message}", title="Error", border_style="red", box=ROUNDED))
        if ctx.obj['verbose']:
            console.print_exception()
        sys.exit(e.exit_code)


@cli.command('diff', short_help="Show diff to be reviewed")
@click.argument('diff_args', nargs=-1)
@click.pass_context
def diff_command(ctx: click.Context, diff_args: List[str]) -> None:
    """
    Show the diff that would be sent for review.
    
    This is useful to preview what will be sent to the AI service.
    DIFF_ARGS are passed directly to 'git diff'. If not provided, 
    staged changes (--cached) will be used.
    """
    try:
        diff_text = get_git_diff(list(diff_args))
        if not diff_text.strip():
            console.print(Panel("No changes found.", title="Information", border_style="yellow", box=ROUNDED))
            return
        
        # Use colorized output if available
        try:
            subprocess.run(["git", "diff", "--color=always"] + list(diff_args) if diff_args else ["git", "diff", "--color=always", "--cached"], check=True)
        except subprocess.CalledProcessError:
            # Fall back to plain text if color diff fails
            console.print(Panel(diff_text, title="Git Diff", border_style="blue", box=ROUNDED))
    
    except PrReviewError as e:
        console.print(Panel(f"Error: {e.message}", title="Error", border_style="red", box=ROUNDED))
        if ctx.obj['verbose']:
            console.print_exception()
        sys.exit(e.exit_code)


@cli.group('config', short_help="Manage configuration")
def config_command() -> None:
    """
    Manage PR Review configuration.
    
    Configuration is stored in ~/.pr-review.toml and follows these priorities:
    CLI flags > Environment variables > Config file > Defaults
    """
    pass


@config_command.command('list')
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """List all configuration values."""
    config = ctx.obj['config']
    
    # Format config for display
    config_lines = ["Current Configuration:"]
    
    for key, value in config.items():
        if key == 'api_keys':
            config_lines.append(f"{key}:")
            for provider, api_key in value.items():
                masked_key = "****" if api_key else "<not set>"
                config_lines.append(f"  {provider}: {masked_key}")
        else:
            config_lines.append(f"{key}: {value}")
    
    console.print(Panel("\n".join(config_lines), title="Configuration", border_style="cyan", box=ROUNDED))


@config_command.command('get')
@click.argument('key', required=True)
@click.pass_context
def config_get(ctx: click.Context, key: str) -> None:
    """Get a specific configuration value."""
    config = ctx.obj['config']
    
    # Handle nested keys (e.g., "api_keys.gemini")
    if '.' in key:
        parts = key.split('.')
        value = config
        for part in parts:
            if part not in value:
                console.print(Panel(f"Key '{key}' not found in config", title="Warning", border_style="yellow", box=ROUNDED))
                return
            value = value[part]
    else:
        if key not in config:
            console.print(Panel(f"Key '{key}' not found in config", title="Warning", border_style="yellow", box=ROUNDED))
            return
        value = config[key]
    
    # Mask API keys
    if 'api_key' in key:
        value = "****" if value else "<not set>"
    
    console.print(Panel(f"{key}: {value}", title="Configuration Value", border_style="cyan", box=ROUNDED))


@config_command.command('set')
@click.argument('key', required=True)
@click.argument('value', required=True)
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value."""
    config = ctx.obj['config']
    
    # Handle nested keys (e.g., "api_keys.gemini")
    if '.' in key:
        parts = key.split('.')
        target = config
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            elif not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        
        # Convert value to appropriate type if needed
        if value.lower() in ('true', 'false'):
            parsed_value = value.lower() == 'true'
        elif value.isdigit():
            parsed_value = int(value)
        else:
            parsed_value = value
            
        target[parts[-1]] = parsed_value
    else:
        # Convert value to appropriate type if needed
        if value.lower() in ('true', 'false'):
            config[key] = value.lower() == 'true'
        elif value.isdigit():
            config[key] = int(value)
        else:
            config[key] = value
    
    # Save the updated config
    save_config(config)
    masked_value = "****" if 'api_key' in key else value
    console.print(Panel(f"Updated: {key} = {masked_value}", title="Configuration Updated", border_style="green", box=ROUNDED))


@config_command.command('unset')
@click.argument('key', required=True)
@click.pass_context
def config_unset(ctx: click.Context, key: str) -> None:
    """Remove a configuration value."""
    config = ctx.obj['config']
    
    # Handle nested keys (e.g., "api_keys.gemini")
    if '.' in key:
        parts = key.split('.')
        target = config
        for part in parts[:-1]:
            if part not in target:
                console.print(Panel(f"Key '{key}' not found in config", title="Warning", border_style="yellow", box=ROUNDED))
                return
            target = target[part]
        
        if parts[-1] not in target:
            console.print(Panel(f"Key '{key}' not found in config", title="Warning", border_style="yellow", box=ROUNDED))
            return
        
        del target[parts[-1]]
    else:
        if key not in config:
            console.print(Panel(f"Key '{key}' not found in config", title="Warning", border_style="yellow", box=ROUNDED))
            return
        
        del config[key]
    
    # Save the updated config
    save_config(config)
    console.print(Panel(f"Removed: {key}", title="Configuration Updated", border_style="green", box=ROUNDED))


# Shell completion command
@cli.command('completion', help="Generate shell completion script")
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def completion_command(shell):
    """Generate shell completion script for the specified shell."""
    completion_script = None
    
    if shell == 'bash':
        completion_script = f"""
# pr-review bash completion script
_pr_review_completion() {{
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${{COMP_WORDS[*]}}" COMP_CWORD=$COMP_CWORD _PR_REVIEW_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"
        if [[ $type == 'dir' ]]; then
            COMPREPLY=( $(compgen -d -- "$value") )
            return
        elif [[ $type == 'file' ]]; then
            COMPREPLY=( $(compgen -f -- "$value") )
            return
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done
}}

complete -o nospace -F _pr_review_completion pr-review
"""
    elif shell == 'zsh':
        completion_script = f"""
#compdef pr-review

_pr_review_completion() {{
    local -a completions
    local -a completions_with_descriptions
    local -a response
    
    response=("$(_PR_REVIEW_COMPLETE=zsh_complete "$words[1]")")
    
    for key descr in ${{(z)response}}; do
        if [[ "$descr" == "_" ]]; then
            completions+=("$key")
        else
            completions_with_descriptions+=("$key:$descr")
        fi
    done
    
    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi
    
    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
    compstate[insert]="automenu"
}}

compdef _pr_review_completion pr-review
"""
    elif shell == 'fish':
        completion_script = f"""
function __fish_pr_review_complete
    set -l response (env _PR_REVIEW_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) pr-review)
    for completion in $response
        set -l metadata (string split "," $completion)
        if test $metadata[1] = "dir"
            __fish_complete_directories $metadata[2]
        else if test $metadata[1] = "file"
            __fish_complete_path $metadata[2]
        else if test $metadata[1] = "plain"
            echo $metadata[2]
        end
    end
end

complete --no-files -c pr-review -a "(__fish_pr_review_complete)"
"""
    
    if completion_script:
        console.print(Panel(completion_script, title=f"{shell.upper()} Completion Script", border_style="blue", box=ROUNDED))
        
        console.print(Panel(
            f"Save the above script to the appropriate location for {shell} completion\n\n"
            f"Example for {shell}:\n"
            + {
                'bash': "Save to ~/.pr-review-completion.bash and add 'source ~/.pr-review-completion.bash' to ~/.bashrc",
                'zsh': "Save to ~/.zfunc/_pr-review and add 'fpath+=~/.zfunc' to ~/.zshrc",
                'fish': "Save to ~/.config/fish/completions/pr-review.fish"
            }[shell],
            title="Installation Instructions", 
            border_style="cyan",
            box=ROUNDED
        ))
    else:
        console.print(Panel(f"Unsupported shell '{shell}'", title="Error", border_style="red", box=ROUNDED))


def main():
    try:
        # Run the CLI
        cli(obj={})
    except Exception as e:
        console.print(Panel(f"Unexpected error: {str(e)}", title="Error", border_style="red", box=ROUNDED))
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()