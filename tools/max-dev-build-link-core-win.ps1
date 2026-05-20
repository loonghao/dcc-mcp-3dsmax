# Build dcc-mcp-core with the target 3ds Max's Python, then link core + dcc-mcp-3dsmax into
# 3ds Max's scripts directory for live debugging (no wheel copy).
#
# Prerequisites: Rust (cargo) on PATH, Git, optional vx on PATH for stubgen fallback.
#
# Usage:
#   .\tools\max-dev-build-link-core-win.ps1 -MaxVersion 2024
#   .\tools\max-dev-build-link-core-win.ps1 -MaxVersion 2024 -CoreRepo G:\path\to\dcc-mcp-core
#   .\tools\max-dev-build-link-core-win.ps1 -MaxVersion 2024 -LaunchMax
#
# Environment:
#   DCC_MCP_CORE_REPO — override path to dcc-mcp-core (default: sibling of this git repo)
#
# 3ds Max 2022+ bundles Python. We use this Python to build dcc-mcp-core with maturin develop,
# then symlink both dcc_mcp_core and dcc_mcp_3dsmax into 3ds Max's scripts directory.

param(
    [string]$MaxVersion = "2024",
    [string]$CoreRepo = "",
    [switch]$SkipBuild,
    [switch]$LaunchMax
)

$ErrorActionPreference = "Stop"

$MaxRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $MaxRoot) {
    $MaxRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if (-not $CoreRepo) {
    if ($env:DCC_MCP_CORE_REPO) {
        $CoreRepo = $env:DCC_MCP_CORE_REPO
    } else {
        $sibling = Join-Path (Split-Path $MaxRoot -Parent) "dcc-mcp-core"
        if (Test-Path (Join-Path $sibling "Cargo.toml")) {
            $CoreRepo = $sibling
        }
    }
}
if (-not $CoreRepo -or -not (Test-Path (Join-Path $CoreRepo "Cargo.toml"))) {
    Write-Error "dcc-mcp-core not found. Clone it next to dcc-mcp-3dsmax or set DCC_MCP_CORE_REPO / -CoreRepo."
}

$CoreRepo = (Resolve-Path $CoreRepo).Path

# Detect 3ds Max installation
$MaxInstallDir = ""
$MaxExe = ""

# Try ADSK_3DSMAX_<version> environment variable
$envVarName = "ADSK_3DSMAX_$($MaxVersion.Replace('.', '_'))"
if ($env:$envVarName) {
    $MaxInstallDir = $env:$envVarName
    $MaxExe = Join-Path $MaxInstallDir "3dsmax.exe"
}

# Fallback: default installation path
if (-not $MaxExe -or -not (Test-Path $MaxExe)) {
    $MaxInstallDir = "C:\Program Files\Autodesk\3ds Max $MaxVersion"
    $MaxExe = Join-Path $MaxInstallDir "3dsmax.exe"
}

# Detect Python in 3ds Max installation
$MaxPython = ""

# Try to find python.exe in 3ds Max directory
if (Test-Path $MaxInstallDir) {
    $MaxPython = Get-ChildItem -Path $MaxInstallDir -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue | 
                    Select-Object -First1 -ExpandProperty FullName
}

# Fallback: use system Python
if (-not $MaxPython -or -not (Test-Path $MaxPython)) {
    Write-Host "   ⚠️  3ds Max Python not found, using system python" -ForegroundColor Yellow
    $MaxPython = "python"
}

$PyTag = & $MaxPython -c "import sys; print('%d.%d' % (sys.version_info[0], sys.version_info[1]))" 2>$null
if (-not $PyTag) {
    Write-Host "   ⚠️  Failed to get Python version, using default features" -ForegroundColor Yellow
    $PyTag = "3.9"
}

Write-Host "   Detected Python $PyTag (from $MaxPython)" -ForegroundColor Gray

# Features for maturin develop
$OptFeatures = "workflow,scheduler,prometheus,job-persist-sqlite"
if ([version]$PyTag -ge [version]"3.8") {
    $DevFeatures = "python-bindings,ext-module,abi3-py38,$OptFeatures"
    Write-Host "   Features: DEV + abi3-py38 (stable ABI)" -ForegroundColor Gray
} else {
    $DevFeatures = "python-bindings,ext-module,$OptFeatures"
    Write-Host "   Features: DEV (no abi3)" -ForegroundColor Gray
}

Write-Host "=== dcc-mcp-core (maturin develop via 3ds Max Python) ===" -ForegroundColor Cyan
Write-Host "   Core repo : $CoreRepo"
Write-Host "   Python    : $MaxPython"
Write-Host ""

if (-not $SkipBuild) {
    Push-Location $CoreRepo
    try {
        Write-Host "   Running stub_gen (cargo)..." -ForegroundColor Gray
        & cargo run -q --bin stub_gen --features stub-gen
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ⚠️  stub_gen failed (exit $LASTEXITCODE); continuing — run manually in core if needed" -ForegroundColor Yellow
        }

        & $MaxPython -m pip install -q --upgrade pip
        & $MaxPython -m pip install -q maturin

        $coreNativeDir = Join-Path $CoreRepo "python\dcc_mcp_core"
        Get-ChildItem -Path $coreNativeDir -Filter "_core*.pyd" -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "   Removing stale $($_.Name) before rebuild" -ForegroundColor Gray
            Remove-Item $_.FullName -Force
        }

        Write-Host "   maturin develop --features $DevFeatures ..." -ForegroundColor Gray
        & $MaxPython -m maturin develop --features $DevFeatures
        if ($LASTEXITCODE -ne 0) { throw "maturin develop failed" }

        # Build the standalone dcc-mcp-server binary for sidecar mode
        Write-Host "   cargo build --release -p dcc-mcp-server ..." -ForegroundColor Gray
        & cargo build --release -p dcc-mcp-server
        if ($LASTEXITCODE -ne 0) { throw "cargo build dcc-mcp-server failed" }
    } finally {
        Pop-Location
    }

    $corePkg = Join-Path $CoreRepo "python\dcc_mcp_core"
    if (-not (Test-Path $corePkg)) {
        Write-Error "Expected package dir missing after build: $corePkg"
    }
    Write-Host "   ✅ dcc_mcp_core built under $corePkg" -ForegroundColor Green
} else {
    Write-Host "   SkipBuild: not rebuilding core" -ForegroundColor Yellow
}

# Resolve the sidecar binary path
$ServerBin = Join-Path $CoreRepo "target\release\dcc-mcp-server.exe"
if (-not (Test-Path $ServerBin)) {
    Write-Host "   ⚠️  dcc-mcp-server.exe not found at $ServerBin" -ForegroundColor Yellow
    $ServerBin = $null
} else {
    Write-Host "   ✅ dcc-mcp-server binary at $ServerBin" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 3ds Max scripts link (core + 3dsmax) ===" -ForegroundColor Cyan

# 3ds Max scripts directory
$ScriptsDir = Join-Path $env:APPDATA "Autodesk\3ds Max $MaxVersion\scripts"
$Target = Join-Path $ScriptsDir "dcc_mcp_3dsmax"
$Pkg3dsMax = Join-Path $MaxRoot "src\dcc_mcp_3dsmax"
$PkgCore = Join-Path $CoreRepo "python\dcc_mcp_core"
$PkgCoreParent = Join-Path $CoreRepo "python"

if (-not (Test-Path $Pkg3dsMax)) { Write-Error "Missing $Pkg3dsMax" }
if (-not $SkipBuild -and -not (Test-Path $PkgCore)) { Write-Error "Missing $PkgCore — build core first (remove -SkipBuild)" }

New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null
if (Test-Path $Target) {
    Remove-Item $Target -Recurse -Force
    Write-Host "   Removed old $Target" -ForegroundColor Gray
}

# Create symbolic link for dcc_mcp_3dsmax
try {
    New-Item -ItemType SymbolicLink -Path $Target -Target $Pkg3dsMax -ErrorAction Stop | Out-Null
    Write-Host "   ✅ $Target → $Pkg3dsMax" -ForegroundColor Green
} catch {
    Write-Error "Symlink dcc_mcp_3dsmax failed (enable Windows Developer Mode or run elevated): $_"
}

# For dcc_mcp_core, create a .pth file in scripts directory to add to sys.path
$corePthPath = Join-Path $ScriptsDir "dcc_mcp_core.pth"
try {
    $PkgCoreParent | Out-File -FilePath $corePthPath -Encoding ASCII
    Write-Host "   ✅ Created $corePthPath (adds dcc_mcp_core parent to sys.path)" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Cannot create .pth file: $_" -ForegroundColor Yellow
    
    # Fallback: create symlink
    $coreLinkPath = Join-Path $ScriptsDir "dcc_mcp_core"
    try {
        if (Test-Path $coreLinkPath) { Remove-Item $coreLinkPath -Force }
        New-Item -ItemType SymbolicLink -Path $coreLinkPath -Target $PkgCore -ErrorAction Stop | Out-Null
        Write-Host "   ✅ $coreLinkPath → $PkgCore" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Cannot symlink dcc_mcp_core: $_" -ForegroundColor Yellow
    }
}

# Create a startup script to set up environment
$StartupScript = Join-Path $ScriptsDir "dcc_mcp_3dsmax_startup.py"
$startupContent = @"
# dcc-mcp-3dsmax startup script (auto-generated by max-dev-build-link-core-win.ps1)
# This file adds dcc_mcp_core and dcc_mcp_3dsmax to sys.path

import sys
from pathlib import Path

# Add dcc_mcp_core to path
core_path = r"$PkgCoreParent"
if core_path not in sys.path:
    sys.path.insert(0, core_path)

# Verify imports
try:
    import dcc_mcp_core
    print("✓ dcc_mcp_core loaded from: $PkgCore")
except ImportError as e:
    print(f"✗ Failed to import dcc_mcp_core: {e}")

try:
    import dcc_mcp_3dsmax
    print("✓ dcc_mcp_3dsmax loaded")
    dcc_mcp_3dsmax.install_menu()
    dcc_mcp_3dsmax.install_shutdown_callback()
    print("✓ dcc-mcp-3dsmax menu and shutdown callback installed")
except ImportError as e:
    print(f"✗ Failed to import dcc_mcp_3dsmax: {e}")
"@

try {
    $startupContent | Out-File -FilePath $StartupScript -Encoding UTF8
    Write-Host "   ✅ Created $StartupScript" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Cannot create startup script: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. Start 3ds Max $MaxVersion and in MAXScript Listener run:" -ForegroundColor Cyan
Write-Host "   python.ExecuteFile @\"$StartupScript\"" -ForegroundColor Gray
Write-Host "This installs the DCC MCP menu; use DCC MCP > Start Sidecar to start the bridge." -ForegroundColor Gray
Write-Host ""
Write-Host "MCP (Streamable HTTP, default):" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:9765/mcp"
Write-Host "Docs: See dcc-mcp-3dsmax docs for Cursor/3ds Max MCP setup" -ForegroundColor Gray

if ($LaunchMax -and (Test-Path $MaxExe)) {
    Write-Host "Launching $MaxExe ..." -ForegroundColor Cyan
    Start-Process -FilePath $MaxExe
} elseif ($LaunchMax) {
    Write-Host "   ⚠️  3ds Max not found at $MaxExe" -ForegroundColor Yellow
}
