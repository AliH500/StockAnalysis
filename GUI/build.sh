#!/usr/bin/env bash
# Build a single-file executable of the Stock Analysis GUI via PyInstaller.
#
# Run from the project root:
#   bash GUI/build.sh
#
# Output: dist/StockAnalysis  (Linux x86_64, ~100-150 MB).
# To produce a Windows .exe, run this same script on a Windows machine (with
# Python 3.11+ and the deps from GUI/requirements.txt installed). Cross-
# building for Windows from Linux requires Wine and is not supported here.

set -euo pipefail

cd "$(dirname "$0")/.."  # repo root (parent of GUI/)

NAME="StockAnalysis"
ENTRY="GUI/main.py"

# Asset bundling: PyInstaller's --add-data uses ":" as the SRC/DEST separator
# on Linux/Mac and ";" on Windows. We're building on Linux here.
SEP=":"

python3 -m PyInstaller \
    --noconfirm \
    --clean \
    --onefile \
    --windowed \
    --name "$NAME" \
    --paths GUI \
    --add-data "GUI/fonts/Nunito-Medium.ttf${SEP}fonts" \
    --add-data "StockAnalysis.py${SEP}v1" \
    --add-data "Segment_tree_adt.py${SEP}v1" \
    --collect-all customtkinter \
    --collect-all tkcalendar \
    --hidden-import PIL._tkinter_finder \
    "$ENTRY"

echo
echo "Built: dist/$NAME"
ls -lh "dist/$NAME"
