"""Output formatters for PR Review CLI."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.box import ROUNDED
from rich.rule import Rule
from rich.syntax import Syntax
from typing import Any, List, Dict, Tuple

console = Console()

def highlight_diff(diff_text: str) -> None:
    """
    Syntax highlight a git diff and print it to the console.
    
    Args:
        diff_text: The git diff text to highlight
    """
    if not diff_text.strip():
        console.print("[yellow]No changes found.[/]")
        return
    
    # Split the diff into files for better presentation
    files = []
    current_file = []
    current_file_name = None
    
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            if current_file and current_file_name:
                files.append((current_file_name, '\n'.join(current_file)))
            current_file = [line]
            # Extract filename from diff --git line
            parts = line.split()
            if len(parts) >= 3:
                current_file_name = parts[2].lstrip('a/')
            else:
                current_file_name = "unknown"
        else:
            current_file.append(line)
    
    # Add the last file
    if current_file and current_file_name:
        files.append((current_file_name, '\n'.join(current_file)))
    
    # Display each file with syntax highlighting
    for i, (filename, content) in enumerate(files):
        if i > 0:
            console.print(Rule())
        
        console.print(f"[bold blue]{filename}[/]")
        syntax = Syntax(content, "diff", theme="monokai", line_numbers=True)
        console.print(syntax)


def print_response(response_stream: Any) -> bool:
    """
    Print the formatted response from the AI provider in real-time as it streams.
    
    Args:
        response_stream: The response stream from the AI provider
        
    Returns:
        bool: True if the review passed (APPROVED), False if it failed (MAKE CHANGES)
    """
    # Create a live display area
    from rich.live import Live
    from rich.markdown import Markdown
    
    # Initialize an empty response
    full_text = ""
    
    # Use Rich's Live display to update content in real-time
    with Live(
        Markdown(full_text),
        console=console,
        refresh_per_second=4,
        vertical_overflow="visible",
        transient=False
    ) as live:
        # Process each chunk as it arrives
        for chunk in response_stream:
            if hasattr(chunk, "text"):
                # Append the new chunk to our accumulated text
                full_text += chunk.text
                # Update the display with the current accumulated text
                live.update(Markdown(full_text))
    
    # Final display with panel after streaming is complete
    console.print(Panel(Markdown(full_text), title="AI PR Review", border_style="green", box=ROUNDED))
    
    # Check if the response contains "MAKE CHANGES"
    if "MAKE CHANGES" in full_text.upper():
        if "Conclusion: MAKE CHANGES" in full_text:
            console.print("\n[bold red]Review failed: Changes requested[/]")
        return False
    else:
        if "Conclusion: APPROVED" in full_text:
            console.print("\n[bold green]Review passed: Approved[/]")
        return True


def format_help_sections(help_text: str) -> None:
    """
    Format and display help text in sections with rich styling.
    
    Args:
        help_text: The raw help text from Click
    """
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