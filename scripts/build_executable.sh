#!/usr/bin/env bash
set -euo pipefail

# Gera um executável único via PyInstaller.
python -m pip install --upgrade pyinstaller
pyinstaller --onefile --name nablaclaw src/nablaclaw/cli.py

echo "Executável gerado em: dist/nablaclaw"
