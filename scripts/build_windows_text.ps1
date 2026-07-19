$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistantText.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\Poro-TextIndex\Poro-TextIndex.exe"
Write-Host ""
Write-Host "Give users the whole dist\Poro-TextIndex folder. This build uses the bundled text index."
