$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

if (-not $env:PYTHON_BIN) {
    $env:PYTHON_BIN = "python"
}

& $env:PYTHON_BIN -m pip install --upgrade "pip<25" setuptools wheel
& $env:PYTHON_BIN -m pip install -r requirements.txt -c packaging/constraints-legacy.txt
& $env:PYTHON_BIN -m pip install -r packaging/requirements-build-legacy.txt

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller --clean --noconfirm `
  --name "FanxingStudyFlow" `
  --onefile `
  --noconsole `
  --add-data "app;app" `
  --add-data "config;config" `
  --collect-all ddddocr `
  --collect-all onnxruntime `
  launcher.py

New-Item -ItemType Directory -Force release | Out-Null
Compress-Archive -Force -Path dist\FanxingStudyFlow.exe -DestinationPath release\FanxingStudyFlow-windows7-win11-x64.zip
