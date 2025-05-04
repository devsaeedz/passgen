#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
import shutil
import site

def print_status(message):
    print("\n" + "="*80)
    print(f"  {message}")
    print("="*80)

def get_pyinstaller_path():
    system = platform.system().lower()
    
    if system == "windows":
        # On Windows, look for PyInstaller in Scripts directory
        for path in site.getsitepackages():
            pyinstaller_path = os.path.join(path, "Scripts", "pyinstaller.exe")
            if os.path.exists(pyinstaller_path):
                return pyinstaller_path
        
        # If not found in site-packages, try user site-packages
        if hasattr(site, 'getusersitepackages'):
            user_site = site.getusersitepackages()
            pyinstaller_path = os.path.join(user_site, "Scripts", "pyinstaller.exe")
            if os.path.exists(pyinstaller_path):
                return pyinstaller_path
    else:
        # On Linux/Mac, try user's local bin first
        user_bin = os.path.expanduser("~/.local/bin/pyinstaller")
        if os.path.exists(user_bin):
            return user_bin
        
        # Then try site-packages
        for path in site.getsitepackages():
            pyinstaller_path = os.path.join(path, "bin", "pyinstaller")
            if os.path.exists(pyinstaller_path):
                return pyinstaller_path
    
    return "pyinstaller"

def install_requirements():
    print_status("Installing build requirements")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyinstaller"])

def clean_build_files():
    print_status("Cleaning up build artifacts")
    
    dirs_to_clean = ['build', '__pycache__']
    
    if os.path.exists('passgen.spec'):
        os.remove('passgen.spec')
        print("Removed spec file")
    
    # Remove directories
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed directory: {dir_name}")

def build_executable():
    system = platform.system().lower()
    
    print_status(f"Building PassGen executable for {system}")
    
    # Clean build files first
    clean_build_files()
    
    # Get the path to PyInstaller
    pyinstaller_path = get_pyinstaller_path()
    print(f"Using PyInstaller at: {pyinstaller_path}")
    
    # Base command
    cmd = [
        pyinstaller_path,
        "--onefile",
        "--clean",
        "--name", "passgen",
        "--hidden-import", "sys",
        "--hidden-import", "os",
        "--hidden-import", "multiprocessing",
        "--hidden-import", "_bootlocale",  # Fix for older PyInstaller versions
    ]
    
    # Add icon for Windows
    if system == "windows":
        pass
    
    # Add the main script
    cmd.append("passgen.py")
    
    # Run the build command
    print("Running PyInstaller with command:")
    print(" ".join(cmd))
    subprocess.check_call(cmd)
    
    # Get the path to the executable
    if system == "windows":
        exe_path = os.path.join("dist", "passgen.exe")
    else:
        exe_path = os.path.join("dist", "passgen")
    
    # Make executable on Unix-like systems
    if system != "windows" and os.path.exists(exe_path):
        os.chmod(exe_path, 0o755)  # rwxr-xr-x
    
    if os.path.exists(exe_path):
        print_status(f"Build successful! Executable created at: {os.path.abspath(exe_path)}")
        
        # Instructions for running
        if system == "windows":
            print("\nTo run the executable, use:")
            print(f"  .\\{exe_path}")
        else:
            print("\nTo run the executable, use:")
            print(f"  ./{exe_path}")
    else:
        print_status("Build failed: Executable not found")

def build_fallback_launcher():
    system = platform.system().lower()
    
    if system != "windows":
        print_status("Creating fallback launcher script")
        
        launcher_path = "passgen.sh"
        with open(launcher_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('# Launcher for PassGen\n\n')
            f.write('# Get the directory where this script is located\n')
            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"\n\n')
            f.write('# Run the Python script with all arguments passed to this script\n')
            f.write('python3 "$SCRIPT_DIR/passgen.py" "$@"\n')
        
        os.chmod(launcher_path, 0o755)
        print(f"Created launcher script at: {os.path.abspath(launcher_path)}")
        print("You can use this if the PyInstaller executable doesn't work.")

def main():
    print_status("PassGen Build Script")
    
    try:
        install_requirements()
        build_executable()
        build_fallback_launcher()  # Create a fallback launcher script
    except subprocess.CalledProcessError as e:
        print(f"\nError during build process: {e}")
        print("\nFalling back to creating launcher script...")
        build_fallback_launcher()
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("\nFalling back to creating launcher script...")
        build_fallback_launcher()
        sys.exit(1)

if __name__ == "__main__":
    main() 