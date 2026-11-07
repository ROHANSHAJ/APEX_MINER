#!/usr/bin/env python3
"""
ApexMiner Setup Binaries Tool
Automatically downloads and configures native miner engines for your operating system.
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "app"))

from binary_downloader import download_and_extract, check_binaries_installed, BIN_DIR

def main():
    print("==========================================================")
    print("       ApexMiner Studio - Binary Setup Engine")
    print("==========================================================")
    print(f"Target Directory: {BIN_DIR}")
    
    if check_binaries_installed():
        print("✓ Native mining binaries are already installed and ready.")
        return 0

    print("Fetching latest native miner engines from GitHub...")
    success, msg = download_and_extract(progress_cb=print)
    if success:
        print("✓ All native binaries configured successfully!")
        return 0
    else:
        print(f"✕ Failed to configure binaries: {msg}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
