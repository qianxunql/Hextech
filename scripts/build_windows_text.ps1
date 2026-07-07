$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistantText.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\HextechAssistant-TextIndex.exe"
Write-Host ""
Write-Host "This build uses the bundled text index. Users only need to set their DeepSeek API Key in the app settings."
