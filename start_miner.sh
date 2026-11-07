#!/usr/bin/env bash
# ==============================================================================
# ApexMiner Studio Launcher - Universal Edition
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/app:${PYTHONPATH}"

if [ -z "$DISPLAY" ]; then
    export DISPLAY=:1
fi

echo "=========================================================="
echo " Starting ApexMiner Studio (Universal Multi-GPU & CPU Mining Suite)..."
echo " Directory: ${SCRIPT_DIR}"
echo "=========================================================="

python3 "${SCRIPT_DIR}/app/main.py" "$@"
