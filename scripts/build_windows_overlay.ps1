$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechOverlay.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\Poro-Overlay\Poro-Overlay.exe"
Write-Host ""
Write-Host "Give users the whole dist\Poro-Overlay folder. This overlay build stays on top and uses the bundled text index plus built-in OCR."
