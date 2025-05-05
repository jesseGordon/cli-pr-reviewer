#!/usr/bin/env python3
"""
CLI reviewer for pull requests - Wrapper script for backwards compatibility.

This standalone script provides backwards compatibility for installations
that used the original single-file version. It simply imports from the
refactored package structure and runs the main function.

For new installations, it's recommended to install as a package using pip or pipx:
    pip install .
    # or
    pipx install .
"""

# Import the main function from the package
try:
    from pr_review.cli import main
except ImportError:
    # If the package is not installed, help the user install it
    import sys
    print("Error: Could not import pr_review package.")
    print("Please install the package using one of these methods:")
    print("  pip install .")
    print("  pipx install .")
    print("  python setup.py install")
    sys.exit(1)

if __name__ == "__main__":
    # Just call the main function from the package
    main()