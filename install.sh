#!/usr/bin/env bash
# ==============================================================================
# ApexMiner Studio - Universal Linux Installer
# Automated installer for Ubuntu, Debian, Fedora, Arch, and RHEL-based systems.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "=========================================================="
echo "      🚀 ApexMiner Studio - Universal Linux Installer"
echo "=========================================================="
echo "Directory: ${SCRIPT_DIR}"

# 1. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 was not found on your system."
    echo "Please install Python 3.8+ (e.g., sudo apt install python3 python3-pip python3-tk)"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python ${PY_VER} detected."

# 2. Check Tkinter
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "⚠️ Python Tkinter is not installed."
    echo "Attempting to install python3-tk..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y python3-tk || true
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-tkinter || true
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm tk || true
    fi
fi

# 3. Install Python Dependencies
echo ""
echo "📦 Installing required Python dependencies..."
python3 -m pip install -r requirements.txt --quiet || python3 -m pip install -r requirements.txt --user --quiet

# 4. Download and setup native mining binaries
echo ""
echo "⚙️ Setting up native mining binaries (Rigel & XMRig)..."
python3 setup_binaries.py

# 5. Make helper scripts executable
chmod +x start_miner.sh launch_hud.sh setup_binaries.py

# 6. Setup Desktop Shortcuts
DESKTOP_DIR="${HOME}/Desktop"
LOCAL_APP_DIR="${HOME}/.local/share/applications"
mkdir -p "${LOCAL_APP_DIR}"

# Remove any legacy duplicate desktop entries
rm -f "${LOCAL_APP_DIR}/apexminer.desktop" "${DESKTOP_DIR}/apexminer.desktop" 2>/dev/null || true

ICON_PATH="${SCRIPT_DIR}/icon.png"

# ApexMiner Studio Desktop Entry
cat << EOF > "${LOCAL_APP_DIR}/ApexMiner.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=ApexMiner Studio
Comment=Universal Multi-GPU & CPU Cryptocurrency Mining Suite
Exec=${SCRIPT_DIR}/start_miner.sh
Icon=${ICON_PATH}
Path=${SCRIPT_DIR}
Terminal=false
Categories=Utility;Finance;
StartupNotify=true
EOF

chmod +x "${LOCAL_APP_DIR}/ApexMiner.desktop"

# Cyber HUD Desktop Entry
cat << EOF > "${LOCAL_APP_DIR}/CyberHUD.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Cyber HUD Visualizer
Comment=Sci-Fi Fullscreen Mining Telemetry Cockpit
Exec=${SCRIPT_DIR}/launch_hud.sh
Icon=${ICON_PATH}
Path=${SCRIPT_DIR}
Terminal=false
Categories=Utility;Graphics;
StartupNotify=true
EOF

chmod +x "${LOCAL_APP_DIR}/CyberHUD.desktop"

if [ -d "${DESKTOP_DIR}" ]; then
    cp "${LOCAL_APP_DIR}/ApexMiner.desktop" "${DESKTOP_DIR}/"
    cp "${LOCAL_APP_DIR}/CyberHUD.desktop" "${DESKTOP_DIR}/"
    chmod +x "${DESKTOP_DIR}/ApexMiner.desktop"
    chmod +x "${DESKTOP_DIR}/CyberHUD.desktop"
    if command -v gio &> /dev/null; then
        gio set "${DESKTOP_DIR}/ApexMiner.desktop" metadata::trusted true 2>/dev/null || true
        gio set "${DESKTOP_DIR}/CyberHUD.desktop" metadata::trusted true 2>/dev/null || true
    fi
    echo "✓ Desktop shortcuts installed to ${DESKTOP_DIR}."
fi

# 7. Add local CLI symlink
mkdir -p "${HOME}/.local/bin"
ln -sf "${SCRIPT_DIR}/start_miner.sh" "${HOME}/.local/bin/apexminer"
ln -sf "${SCRIPT_DIR}/launch_hud.sh" "${HOME}/.local/bin/apex-hud"

echo ""
echo "=========================================================="
echo "🎉 Installation Complete!"
echo "=========================================================="
echo "You can launch ApexMiner Studio in 3 ways:"
echo "  1. Double-click 'ApexMiner Studio' on your Desktop"
echo "  2. Run command: apexminer (or ${SCRIPT_DIR}/start_miner.sh)"
echo "  3. Open Cyber HUD Visualizer: apex-hud (or http://127.0.0.1:8765)"
echo "=========================================================="
