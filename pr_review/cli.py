#!/usr/bin/env python3
"""
PR Review CLI - Entry point for the pip-installable package.
"""

# Import the main function from the original script
from . import __version__
import os
import sys

# Import everything from the original script so the module works the same way
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
from rich.syntax import Syntax
from rich.rule import Rule
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import subprocess
import textwrap
import threading
import time
from difflib import get_close_matches

# Import the CLI from the original file
from importlib.util import spec_from_file_location, module_from_spec
import importlib.machinery
import inspect

# Function to get the original cli function from cli-reviewer.py
def get_cli_function():
    """Load the CLI function from the original script."""
    # Get the directory where this package is installed
    package_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(os.path.dirname(package_dir), 'cli-reviewer.py')
    
    # If script doesn't exist in package directory, look for it in a few other places
    if not os.path.exists(script_path):
        possible_paths = [
            os.path.join(os.getcwd(), 'cli-reviewer.py'),
            os.path.join(os.path.dirname(os.getcwd()), 'cli-reviewer.py'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                script_path = path
                break
    
    if not os.path.exists(script_path):
        raise ImportError("Cannot find cli-reviewer.py. Make sure it's in the package directory or current directory.")
    
    # Load the script as a module
    loader = importlib.machinery.SourceFileLoader('cli_reviewer', script_path)
    spec = spec_from_file_location('cli_reviewer', script_path, loader=loader)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the CLI function
    return module.cli, module.main

# Get the CLI function and the main function
cli_function, original_main = get_cli_function()

def main():
    """Entry point for the pip-installable package."""
    # Just call the original main function
    original_main()

if __name__ == "__main__":
    main() 