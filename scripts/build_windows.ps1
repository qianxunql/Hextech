$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistant.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\HextechAssistant.exe"
Write-Host ""
Write-Host "Give this single exe to users. They can set the DeepSeek API Key in the app settings."
