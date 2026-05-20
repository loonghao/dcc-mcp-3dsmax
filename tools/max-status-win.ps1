# max-status-win.ps1
# Show current 3ds Max dev link status
# Usage: just max-status-win  or  powershell -File tools/max-status-win.ps1 -MaxVersion 2024

param(
    [string]$MaxVersion = $env:MAX_VERSION
)

# Default 3ds Max version
if ([string]::IsNullOrEmpty($MaxVersion)) {
    $MaxVersion = "2024"
}

# Detect 3ds Max scripts directory
$AppData = $env:APPDATA
$ScriptsDir = Join-Path $AppData "Autodesk\3ds Max $MaxVersion\scripts"
$Target = Join-Path $ScriptsDir "dcc_mcp_3dsmax"

Write-Host "📋 3ds Max dev link status:" -ForegroundColor Cyan
Write-Host "   Scripts dir: $ScriptsDir"
Write-Host ""

if (Test-Path $Target) {
    $targetItem = Get-Item $Target
    if ($targetItem.LinkType) {
        $realPath = (Get-Item $Target).Target
        Write-Host "   ✅ dcc_mcp_3dsmax → $realPath (symlink)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  dcc_mcp_3dsmax exists (copied, not linked)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ dcc_mcp_3dsmax not found" -ForegroundColor Red
}

# Check dcc_mcp_core.pth file
$corePth = Join-Path $ScriptsDir "dcc_mcp_core.pth"
if (Test-Path $corePth) {
    $corePath = Get-Content $corePth -First 1
    Write-Host "   ✅ dcc_mcp_core.pth exists (points to: $corePath)" -ForegroundColor Green
} else {
    $coreLink = Join-Path $ScriptsDir "dcc_mcp_core"
    if (Test-Path $coreLink) {
        Write-Host "   ✅ dcc_mcp_core → $((Get-Item $coreLink).Target) (symlink)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ dcc_mcp_core not found in scripts directory" -ForegroundColor Red
    }
}

# Check startup script
$startupScript = Join-Path $ScriptsDir "dcc_mcp_3dsmax_startup.py"
if (Test-Path $startupScript) {
    Write-Host "   ✅ Startup script exists: $startupScript" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Startup script not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "   To fix: just max-link-win" -ForegroundColor Gray
Write-Host "   To remove: just max-unlink-win" -ForegroundColor Gray
