"""
Cross-Platform Miner Binary Downloader & Manager
Ensures native mining engines (Rigel, XMRig) exist for Linux & Windows.
"""

import os
import sys
import tarfile
import zipfile
import platform
import urllib.request
import shutil

BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bin"))

# Verified release URLs for Rigel & XMRig
DOWNLOAD_TARGETS = {
    "Linux": {
        "rigel": {
            "url": "https://github.com/rigelminer/rigel/releases/download/1.23.2/rigel-1.23.2-linux.tar.gz",
            "type": "tar.gz",
            "bin_rel": "rigel-1.23.2-linux/rigel",
            "dest_name": "rigel"
        },
        "xmrig": {
            "url": "https://github.com/xmrig/xmrig/releases/download/v6.26.0/xmrig-6.26.0-linux-static-x64.tar.gz",
            "type": "tar.gz",
            "bin_rel": "xmrig-6.26.0/xmrig",
            "dest_name": "xmrig"
        }
    },
    "Windows": {
        "rigel": {
            "url": "https://github.com/rigelminer/rigel/releases/download/1.23.2/rigel-1.23.2-win.zip",
            "type": "zip",
            "bin_rel": "rigel-1.23.2-win/rigel.exe",
            "dest_name": "rigel.exe"
        },
        "xmrig": {
            "url": "https://github.com/xmrig/xmrig/releases/download/v6.26.0/xmrig-6.26.0-msvc-win64.zip",
            "type": "zip",
            "bin_rel": "xmrig-6.26.0/xmrig.exe",
            "dest_name": "xmrig.exe"
        }
    }
}

def get_binary_path(name):
    """Returns absolute path to executable for current platform"""
    os_name = platform.system()
    ext = ".exe" if os_name == "Windows" else ""
    return os.path.join(BIN_DIR, f"{name}{ext}")

def check_binaries_installed():
    """Checks if required binaries exist for current OS"""
    rigel_path = get_binary_path("rigel")
    xmrig_path = get_binary_path("xmrig")
    return os.path.exists(rigel_path) or os.path.exists(xmrig_path)

def download_and_extract(progress_cb=None):
    """Downloads and extracts native mining binaries for current operating system"""
    os_name = platform.system()
    if os_name not in DOWNLOAD_TARGETS:
        return False, f"Unsupported OS: {os_name}"

    os.makedirs(BIN_DIR, exist_ok=True)
    targets = DOWNLOAD_TARGETS[os_name]

    for name, info in targets.items():
        dest_bin = os.path.join(BIN_DIR, info["dest_name"])
        if os.path.exists(dest_bin):
            continue

        if progress_cb:
            progress_cb(f"Downloading {name} for {os_name}...")

        archive_path = os.path.join(BIN_DIR, f"temp_{name}.{info['type']}")
        try:
            req = urllib.request.Request(info["url"], headers={"User-Agent": "ApexMiner-Installer/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(archive_path, "wb") as out:
                shutil.copyfileobj(resp, out)

            # Extraction
            if info["type"] == "tar.gz":
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=BIN_DIR)
            elif info["type"] == "zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(path=BIN_DIR)

            extracted_bin = os.path.join(BIN_DIR, info["bin_rel"])
            if os.path.exists(extracted_bin):
                if os_name != "Windows":
                    os.chmod(extracted_bin, 0o755)
                    # Symlink or copy to standard name
                    if os.path.islink(dest_bin) or os.path.exists(dest_bin):
                        os.remove(dest_bin)
                    os.symlink(extracted_bin, dest_bin)
                else:
                    shutil.copy2(extracted_bin, dest_bin)

            if os.path.exists(archive_path):
                os.remove(archive_path)

        except Exception as e:
            if progress_cb:
                progress_cb(f"Error downloading {name}: {e}")
            return False, str(e)

    return True, "Binaries installed successfully"

if __name__ == "__main__":
    print("Checking and preparing mining binaries...")
    success, msg = download_and_extract(progress_cb=print)
    print("Result:", success, msg)
