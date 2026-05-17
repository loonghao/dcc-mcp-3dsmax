# max-unlink-win.ps1
# Remove dev symlinks from 3ds Max's scripts directory
# Usage: just max-unlink-win  or  powershell -File tools/max-unlink-win.ps1 -MaxVersion 2025

param(
    [string]$MaxVersion = $env:MAX_VERSION
)

# Default 3ds Max version
if ([string]::IsNullOrEmpty($MaxVersion)) {
    $MaxVersion = "2025"
}

# Detect 3ds Max scripts directory
$AppData = $env:APPDATA
$ScriptsDir = Join-Path $AppData "Autodesk\3ds Max $MaxVersion\scripts"
$Target = Join-Path $ScriptsDir "dcc_mcp_3dsmax"

Write-Host "🧹 Removing 3ds Max dev symlinks..." -ForegroundColor Cyan
Write-Host "   Scripts  : $ScriptsDir" -ForegroundColor Gray
Write-Host ""

# Remove dcc_mcp_3dsmax symlink/directory
if (Test-Path $Target) {
    $targetItem = Get-Item $Target
    if ($targetItem.LinkType) {
        Remove-Item $Target -Force
        Write-Host "   ✅ Removed symlink: $Target" -ForegroundColor Green
    } else {
        Remove-Item $Target -Recurse -Force
        Write-Host "   ✅ Removed directory: $Target" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠️  $Target not found (already removed?)" -ForegroundColor Yellow
}

# Remove dcc_mcp_core.pth file if exists
$corePth = Join-Path $ScriptsDir "dcc_mcp_core.pth"
if (Test-Path $corePth) {
    Remove-Item $corePth -Force
    Write-Host "   ✅ Removed: $corePth" -ForegroundColor Green
}

# Remove startup script if exists
$startupScript = Join-Path $ScriptsDir "dcc_mcp_3dsmax_startup.py"
if (Test-Path $startupScript) {
    Remove-Item $startupScript -Force
    Write-Host "   ✅ Removed: $startupScript" -ForegroundColor Green
}

Write-Host ""
Write-Host "   ✅ Dev symlinks cleaned up" -ForegroundColor Green
