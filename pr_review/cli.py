#!/usr/bin/env python3
"""
PR Review CLI - Entry point for the pip-installable package.
"""

import os
import sys
import click
from typing import List, Optional
from pathlib import Path
from rich.panel import Panel
from rich.box import ROUNDED
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from . import __version__
from .exceptions import PrReviewError
from .output import console, highlight_diff, print_response
from .git_utils import get_git_diff
from .config import load_config, save_config
from .ai_providers import send_to_provider, make_prompt
from .cli_helpers import SuggestionGroup, generate_shell_completion


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, cls=SuggestionGroup)
@click.version_option(version=__version__)
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
@click.option('--staged', is_flag=True, help="Review staged changes (default if no option provided)")
@click.option('--unstaged', is_flag=True, help="Review unstaged changes")
@click.option('--file', type=str, help="Review changes in specific file")
@click.option('--commit', type=str, help="Review changes in specific commit or commit range (e.g., SHA or SHA1..SHA2)")
@click.option('--max-chars', type=int, help="Maximum characters to include in the diff")
@click.option('--provider', help="AI provider to use [gemini|openai|anthropic]")
@click.option('--model', help="Specific model to use")
@click.option('--ignore-errors', is_flag=True, help="Always return exit code 0 even if changes requested")
@click.argument('diff_args', nargs=-1)
@click.pass_context
def review_command(ctx: click.Context, staged: bool, unstaged: bool, file: Optional[str], 
                  commit: Optional[str], max_chars: Optional[int], provider: Optional[str], 
                  model: Optional[str], ignore_errors: bool, diff_args: List[str]) -> None:
    """
    Review code changes using AI.
    
    By default, reviews staged changes if no options are provided.
    You can specify different sources of changes with options, or provide
    arguments to be passed directly to 'git diff'.
    
    The command will return exit code 1 if the review suggests changes
    (contains "MAKE CHANGES"), unless --ignore-errors is specified.
    
    Examples:
      pr-review review                  # Review staged changes
      pr-review review --unstaged       # Review unstaged changes
      pr-review review --file path/to/file.js  # Review changes in specific file
      pr-review review --commit abc123  # Review changes in specific commit
      pr-review review --max-chars 5000 # Limit diff size
      pr-review review HEAD~3..HEAD     # Review last 3 commits
      pr-review review --ignore-errors  # Don't exit with non-zero code if changes requested
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
        
        # Get the git diff based on options
        diff_text = get_git_diff(
            staged=staged,
            unstaged=unstaged,
            file_path=file,
            commit=commit,
            diff_args=list(diff_args) if diff_args else None,
            max_chars=max_chars
        )
        
        if not diff_text.strip():
            console.print(Panel("No changes found.", title="Information", border_style="yellow", box=ROUNDED))
            return
        
        # Create the prompt
        prompt = make_prompt(diff_text)
        
        # Show progress while waiting for response
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Reviewing Code Changes..."),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Waiting...", total=None)
            # Send to AI provider and get response
            review_stream = send_to_provider(prompt, active_provider, active_model, api_key)
            
        # Print the review and get the result
        review_passed = print_response(review_stream)
        
        # Exit with appropriate code unless --ignore-errors is specified
        if not ignore_errors and not review_passed:
            sys.exit(1)
        
    except PrReviewError as e:
        console.print(Panel(f"Error: {e.message}", title="Error", border_style="red", box=ROUNDED))
        if ctx.obj['verbose']:
            console.print_exception()
        sys.exit(e.exit_code)


@cli.command('diff', short_help="Show diff to be reviewed")
@click.option('--staged', is_flag=True, help="Show staged changes (default if no option provided)")
@click.option('--unstaged', is_flag=True, help="Show unstaged changes")
@click.option('--file', type=str, help="Show changes in specific file")
@click.option('--commit', type=str, help="Show changes in specific commit or commit range (e.g., SHA or SHA1..SHA2)")
@click.option('--max-chars', type=int, help="Maximum characters to include in the diff")
@click.option('--no-color', is_flag=True, help="Disable syntax highlighting")
@click.argument('diff_args', nargs=-1)
@click.pass_context
def diff_command(ctx: click.Context, staged: bool, unstaged: bool, file: Optional[str], 
                commit: Optional[str], max_chars: Optional[int], no_color: bool, 
                diff_args: List[str]) -> None:
    """
    Show the diff that would be sent for review with syntax highlighting.
    
    By default, shows staged changes if no options are provided.
    You can specify different sources of changes with options, or provide
    arguments to be passed directly to 'git diff'.
    
    Examples:
      pr-review diff                   # Show staged changes
      pr-review diff --unstaged        # Show unstaged changes
      pr-review diff --file path/to/file.js  # Show changes in specific file
      pr-review diff --commit abc123   # Show changes in specific commit
      pr-review diff --max-chars 5000  # Limit diff size
      pr-review diff HEAD~3..HEAD      # Show last 3 commits
    """
    try:
        # Get the git diff based on options
        diff_text = get_git_diff(
            staged=staged,
            unstaged=unstaged,
            file_path=file,
            commit=commit,
            diff_args=list(diff_args) if diff_args else None,
            max_chars=max_chars
        )
        
        if not diff_text.strip():
            console.print(Panel("No changes found.", title="Information", border_style="yellow", box=ROUNDED))
            return
        
        # Show the diff with or without syntax highlighting
        if no_color:
            console.print(diff_text)
        else:
            highlight_diff(diff_text)
    
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
    
    # Format config for display in simplified style
    config_lines = []
    config_lines.append("[bold]Current Configuration:[/]")
    
    for key, value in config.items():
        if key == 'api_keys':
            config_lines.append(f"\n[cyan]{key}:[/]")
            for provider, api_key in value.items():
                masked_key = "****" if api_key else "<not set>"
                config_lines.append(f"  [green]{provider}:[/] {masked_key}")
        else:
            config_lines.append(f"[cyan]{key}:[/] [green]{value}[/]")
    
    console.print("\n".join(config_lines))


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


@cli.command('completion', help="Generate shell completion script")
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def completion_command(shell):
    """Generate shell completion script for the specified shell."""
    completion_script = generate_shell_completion(shell)
    
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
    """Entry point for the pip-installable package."""
    try:
        # Run the CLI
        cli(obj={})
    except Exception as e:
        console.print(Panel(f"Unexpected error: {str(e)}", title="Error", border_style="red", box=ROUNDED))
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main() 