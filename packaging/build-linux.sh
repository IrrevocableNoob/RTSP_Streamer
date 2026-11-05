#!/usr/bin/env bash
# Build a one-file RTSP_Streamer binary on Linux. Run from the repo root:
#   python -m venv .venv && . .venv/bin/activate
#   ./packaging/build-linux.sh
# Output: dist/RTSP_Streamer  (needs system VLC installed to run)
set -euo pipefail
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed \
  --name RTSP_Streamer --paths src \
  --distpath dist --workpath build/pyi --specpath build \
  packaging/launch.py
echo "Built: dist/RTSP_Streamer"
