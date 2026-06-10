#!/usr/bin/env python3
"""OpenAL installation and download helper script for EchoRunner."""
import sys
import os
import urllib.request
import zipfile
import subprocess
from pathlib import Path

def setup_windows():
    print("=" * 60)
    print("           WINDOWS OPENAL SOFT BINARY DOWNLOADER")
    print("=" * 60)
    url = "https://openal-soft.org/openal-binaries/openal-soft-1.23.1-bin.zip"
    zip_path = Path("openal_soft_temp.zip")
    
    root_dir = Path(__file__).parent.parent
    dest_dll = root_dir / "OpenAL32.dll"
    
    print(f"Downloading OpenAL Soft package from: {url}")
    try:
        # User-agent header to avoid potential blocks
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
            
        print("Download complete. Extracting Win64/soft_oal.dll...")
        with zipfile.ZipFile(zip_path, "r") as z:
            # Look for bin/Win64/soft_oal.dll
            target_path = "openal-soft-1.23.1-bin/bin/Win64/soft_oal.dll"
            if target_path in z.namelist():
                dll_data = z.read(target_path)
                dest_dll.write_bytes(dll_data)
                print(f"Successfully placed OpenAL32.dll at: {dest_dll.resolve()}")
                print("Windows OpenAL configuration complete!")
            else:
                print("Error: Could not find Win64 dll inside zip archive.")
    except Exception as e:
        print(f"Error during Windows OpenAL setup: {e}")
        print("Please download manually from https://openal-soft.org/ and rename soft_oal.dll to OpenAL32.dll in the game folder.")
    finally:
        if zip_path.exists():
            zip_path.unlink()

def setup_linux():
    print("=" * 60)
    print("           LINUX OPENAL SYSTEM INSTALLER")
    print("=" * 60)
    
    # Check if libopenal is already present in standard locations
    paths = ["/usr/lib/libopenal.so.1", "/usr/lib64/libopenal.so.1", "/usr/lib/x86_64-linux-gnu/libopenal.so.1"]
    if any(os.path.exists(p) for p in paths):
        print("OpenAL Soft library detected on your system. No further installation needed!")
        return

    # Check package managers
    try:
        if subprocess.run(["which", "apt-get"], capture_output=True).returncode == 0:
            print("Found apt-get. Attempting to install libopenal1...")
            print("Executing: sudo apt-get update && sudo apt-get install -y libopenal1")
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            subprocess.run(["sudo", "apt-get", "install", "-y", "libopenal1"], check=True)
            print("OpenAL successfully installed via apt-get.")
            return
    except Exception as e:
        print(f"Apt install failed or needs passwordless sudo: {e}")

    try:
        if subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
            print("Found dnf. Attempting to install openal-soft...")
            print("Executing: sudo dnf install -y openal-soft")
            subprocess.run(["sudo", "dnf", "install", "-y", "openal-soft"], check=True)
            print("OpenAL successfully installed via dnf.")
            return
    except Exception as e:
        print(f"Dnf install failed: {e}")

    print("-" * 60)
    print("Manual Installation Required:")
    print("Please install OpenAL via your package manager:")
    print("  Ubuntu/Debian: sudo apt-get install libopenal1")
    print("  Fedora/RHEL:   sudo dnf install openal-soft")
    print("  Arch Linux:    sudo pacman -S openal")
    print("-" * 60)

def setup_macos():
    print("=" * 60)
    print("           MACOS OPENAL INSTALLER")
    print("=" * 60)
    
    # Check if Homebrew is installed
    try:
        if subprocess.run(["which", "brew"], capture_output=True).returncode == 0:
            print("Found Homebrew. Running: brew install openal-soft")
            subprocess.run(["brew", "install", "openal-soft"], check=True)
            print("OpenAL successfully installed via Homebrew.")
        else:
            print("Homebrew ('brew') command not found.")
            print("Please install Homebrew (https://brew.sh) and run: brew install openal-soft")
    except Exception as e:
        print(f"Homebrew installation command failed: {e}")
        print("Please run manually: brew install openal-soft")

def main():
    if sys.platform.startswith("win"):
        setup_windows()
    elif sys.platform.startswith("darwin"):
        setup_macos()
    else:
        setup_linux()

if __name__ == "__main__":
    main()
