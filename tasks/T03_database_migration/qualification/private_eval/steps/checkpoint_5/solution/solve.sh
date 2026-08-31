#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

# Wipe /app before copying so files written by a prior checkpoint
# (solution or tests) cannot leak into this snapshot. The trajectory
# payload is the full expected state for this checkpoint.
find /app -mindepth 1 -delete
cp -a "$DIR/payload/." /app/

cd /app
if [ -f requirements.txt ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi

echo "[oracle] Solution copied for checkpoint_5 at $(date -Iseconds)"
