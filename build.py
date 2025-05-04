#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
import shutil

def print_status(message):
    print("\n" + "="*80)
    print(f"  {message}")
    print("="*80)

def install_requirements():
    print_status("Installing build requirements")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

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
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--clean",
        "--name", "passgen",
        "--hidden-import", "sys",
        "--hidden-import", "os",
        "--hidden-import", "multiprocessing",
    ]
    
    # Add icon for Windows
    if system == "windows":
        # Uncomment and update if you have an icon
        # cmd.extend(["--icon", "icon.ico"])
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

def main():
    print_status("PassGen Build Script")
    
    try:
        install_requirements()
        build_executable()
    except subprocess.CalledProcessError as e:
        print(f"\nError during build process: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 