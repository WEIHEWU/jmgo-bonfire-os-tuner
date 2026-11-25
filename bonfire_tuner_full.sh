#!/usr/bin/env bash
# Bonfire OS Tuning Tool N5/N5S — Linux/macOS launcher.
# All logic lives in bonfire_tuner_full.py (cross-platform).

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/bonfire_tuner_full.py"

if [ ! -f "$PY_SCRIPT" ]; then
    echo "[ERROR] bonfire_tuner_full.py not found in script folder." >&2
    exit 1
fi

# Find Python 3
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info[0]==3 else 1)' 2>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 not found in PATH." >&2
    echo "  - macOS: brew install python" >&2
    echo "  - Linux: sudo apt install python3 (or equivalent)" >&2
    exit 1
fi

exec "$PY_CMD" "$PY_SCRIPT" "$@"
