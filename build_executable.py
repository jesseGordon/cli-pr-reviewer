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
    spec_file = Path("pr-review.spec")
    
    for path in [dist_dir, build_dir, spec_file]:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    
    # Create a simple entry point script for PyInstaller
    entry_script = Path("cli_entry_point.py")
    with open(entry_script, "w") as f:
        f.write("""#!/usr/bin/env python3
# Entry point script for PyInstaller
from pr_review.cli import main

if __name__ == "__main__":
    main()
""")
    
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
    
    # Add entry script
    cmd.append(str(entry_script))
    
    try:
        # Run PyInstaller
        subprocess.check_call(cmd)
        
        # Clean up temporary entry point
        entry_script.unlink()
        
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
            
            print("\nTo share with others:")
            print("- Simply send them the executable file")
            print("- They can place it in their PATH and run it directly")
            print("- No Python installation or dependencies required")
        else:
            print(f"Error: Executable not found at {executable_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running PyInstaller: {e}")
        if entry_script.exists():
            entry_script.unlink()

if __name__ == "__main__":
    ensure_pyinstaller()
    build_executable() 