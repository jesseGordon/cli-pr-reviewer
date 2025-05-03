#!/usr/bin/env python3
"""
Build script to create a standalone executable of the PR Review CLI tool.
"""

import os
import subprocess
import platform
import shutil
from pathlib import Path

def ensure_pyinstaller():
    """Ensure PyInstaller is installed"""
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call(["pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building PR Review CLI executable...")
    
    # Determine platform-specific settings
    is_windows = platform.system() == "Windows"
    executable_name = "pr-review.exe" if is_windows else "pr-review"
    
    # Cleanup any previous build artifacts
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("cli-reviewer.spec")
    
    for path in [dist_dir, build_dir, spec_file]:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    
    # Check if we're in a package structure or standalone script
    package_structure = Path("pr_review").exists() and Path("pr_review/__init__.py").exists()
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",                # Create a single file executable
        "--name", "pr-review",      # Name of the output file
        "--clean",                  # Clean PyInstaller cache
        "--noconfirm",              # Replace output directory without asking
    ]
    
    # Add data files
    if is_windows:
        cmd.extend(["--add-data", "README.md;."])
    else:
        cmd.extend(["--add-data", "README.md:."])
    
    # Determine the entry point
    if package_structure:
        print("Building from package structure...")
        # Use the module entry point
        cmd.append("-m")
        cmd.append("pr_review.cli")
    else:
        print("Building from standalone script...")
        # Use the script directly
        cmd.append("cli-reviewer.py")
    
    # Run PyInstaller
    subprocess.check_call(cmd)
    
    # Verify executable was created
    executable_path = dist_dir / executable_name
    if executable_path.exists():
        print(f"Successfully built executable: {executable_path}")
        # Make binary executable on Unix-like systems
        if not is_windows:
            os.chmod(executable_path, 0o755)
        
        print("Installation instructions:")
        print("1. Copy the executable to a directory in your PATH:")
        if is_windows:
            print("   copy dist\\pr-review.exe C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Scripts")
        else:
            print("   sudo cp dist/pr-review /usr/local/bin/")
            print("   # or")
            print("   cp dist/pr-review ~/bin/")
    else:
        print(f"Error: Executable not found at {executable_path}")

if __name__ == "__main__":
    ensure_pyinstaller()
    build_executable() 