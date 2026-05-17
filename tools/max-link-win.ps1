# max-link-win.ps1
# Create symlinks from source tree into 3ds Max's scripts directory for live development
# Usage: just max-link-win  or  powershell -File tools/max-link-win.ps1 -MaxVersion 2025

param(
    [string]$MaxVersion = $env:MAX_VERSION,
    # tools/ → repository root (dcc-mcp-3dsmax), not the monorepo parent
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

# Default 3ds Max version
if ([string]::IsNullOrEmpty($MaxVersion)) {
    $MaxVersion = "2025"
}

# Detect 3ds Max scripts directory
$AppData = $env:APPDATA
$ScriptsDir = Join-Path $AppData "Autodesk\3ds Max $MaxVersion\scripts"
$Target = Join-Path $ScriptsDir "dcc_mcp_3dsmax"

Write-Host "🔗 Setting up 3ds Max dev symlinks (3ds Max $MaxVersion)..." -ForegroundColor Cyan
Write-Host "   Project  : $ProjectRoot" -ForegroundColor Gray
Write-Host "   Scripts  : $ScriptsDir" -ForegroundColor Gray
Write-Host ""

# Create scripts dir if needed
if (!(Test-Path $ScriptsDir)) {
    New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null
    Write-Host "   Created scripts directory" -ForegroundColor Yellow
}

# Remove old link/dir if exists
if (Test-Path $Target) {
    $targetItem = Get-Item $Target
    if ($targetItem.LinkType) {
        # It's a symlink, remove it
        Remove-Item $Target -Force
        Write-Host "   Removed old symlink" -ForegroundColor Yellow
    } else {
        # It's a real directory
        Write-Host "   ⚠️  $Target is a real directory (not a symlink)." -ForegroundColor Yellow
        Write-Host "   Remove it manually if you want to use dev symlinks." -ForegroundColor Yellow
        exit 1
    }
}

# Source directory
$SourceDir = Join-Path $ProjectRoot "src\dcc_mcp_3dsmax"

if (!(Test-Path -LiteralPath $SourceDir)) {
    Write-Host "   ❌ Source not found: $SourceDir" -ForegroundColor Red
    Write-Host "   Fix: run this script from the dcc-mcp-3dsmax repo (or pass -ProjectRoot)." -ForegroundColor Yellow
    exit 1
}

# Create symbolic link
# Requires developer mode or admin privileges
try {
    New-Item -ItemType SymbolicLink -Path $Target -Target $SourceDir -Force -ErrorAction Stop | Out-Null
    Write-Host "   ✅ Symbolic link created successfully" -ForegroundColor Green
    Write-Host "      $Target → $SourceDir" -ForegroundColor Gray
} catch {
    Write-Host "   ⚠️  Symbolic link failed (need admin or Developer Mode), copying instead..." -ForegroundColor Yellow
    try {
        Copy-Item -Path $SourceDir -Destination $Target -Recurse -Force -ErrorAction Stop
        Write-Host "   ✅ Source copied (edits require manual copy)" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ Copy failed: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "   Next: start 3ds Max $MaxVersion and run in MAXScript Listener:" -ForegroundColor Cyan
Write-Host "      python.ExecuteFile @""$Target\__init__.py""" -ForegroundColor Gray
Write-Host "   Or add to startup script: import dcc_mcp_3dsmax" -ForegroundColor Gray
