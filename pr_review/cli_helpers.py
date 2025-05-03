"""CLI helper functions and classes for PR Review CLI."""

import click
from difflib import get_close_matches
from .output import console, format_help_sections
from rich.panel import Panel
from rich.box import ROUNDED

class SuggestionGroup(click.Group):
    """Enhanced Click Group with command suggestions."""
    
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
        format_help_sections(formatter.getvalue())
        ctx.exit()

    def format_subcommand_help(self, original_format_help, ctx, formatter):
        # Call the original format_help to get the help text
        original_format_help(ctx, formatter)
        format_help_sections(formatter.getvalue())
        ctx.exit()


def generate_shell_completion(shell: str) -> str:
    """
    Generate a shell completion script for the specified shell.
    
    Args:
        shell: The shell type (bash, zsh, fish)
        
    Returns:
        str: The completion script for the shell or None if not supported
    """
    if shell == 'bash':
        return """
# pr-review bash completion script
_pr_review_completion() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _PR_REVIEW_COMPLETE=bash_complete $1)

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
}

complete -o nospace -F _pr_review_completion pr-review
"""
    elif shell == 'zsh':
        return """
#compdef pr-review

_pr_review_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    
    response=("$(_PR_REVIEW_COMPLETE=zsh_complete "$words[1]")")
    
    for key descr in ${(z)response}; do
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
}

compdef _pr_review_completion pr-review
"""
    elif shell == 'fish':
        return """
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
    return None 