#!/usr/bin/env bash
# ==============================================================================
# Launch ApexMiner Cyber HUD Cockpit Visualizer
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start visualizer server in background if not already running
if ! pgrep -f "visualizer/server.py" > /dev/null; then
    nohup python3 "${SCRIPT_DIR}/visualizer/server.py" > /dev/null 2>&1 &
    sleep 0.8
fi

# Open in browser
xdg-open "http://127.0.0.1:8765" || sensible-browser "http://127.0.0.1:8765"
