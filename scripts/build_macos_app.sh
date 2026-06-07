#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
export MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-10.13}"

"$PYTHON_BIN" -m pip install --upgrade "pip<25" setuptools wheel
"$PYTHON_BIN" -m pip install -r requirements.txt -c packaging/constraints-legacy.txt
"$PYTHON_BIN" -m pip install -r packaging/requirements-build-legacy.txt

rm -rf build dist
pyinstaller --clean --noconfirm \
  --name "FanxingStudyFlow" \
  --windowed \
  --onedir \
  --target-architecture x86_64 \
  --add-data "app:app" \
  --add-data "config:config" \
  --collect-all ddddocr \
  --collect-all onnxruntime \
  launcher.py

mkdir -p release
tar -czf release/FanxingStudyFlow-macos10.13-x64.tar.gz -C dist FanxingStudyFlow.app
