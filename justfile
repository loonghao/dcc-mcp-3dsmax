# dcc-mcp-3dsmax development justfile
# Unified dependency and task management

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]
set shell := ["bash", "-c"]
set dotenv-load := true

# Default recipe
default:
    @just --list

# ============================================================================
# Dependency Management
# ============================================================================

# Install development dependencies
@install-dev:
    echo "🔧 Installing development dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    echo "✅ Development dependencies installed"

# Install minimal dependencies (production only)
@install-prod:
    echo "🔧 Installing production dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -e .
    echo "✅ Production dependencies installed"

# Install all dependencies (dev + test + build)
@install-all: install-dev
    echo "✅ All dependencies ready"

# Verify dependency installation
@verify-deps:
    echo "🔍 Verifying dependency installation..."
    python -c "from dcc_mcp_3dsmax import start_server; print('✓ dcc_mcp_3dsmax')"
    python -c "from dcc_mcp_core import create_skill_server; print('✓ dcc_mcp_core')"
    python -c "import pytest; print('✓ pytest')"
    python -c "import pymxs" 2>/dev/null && echo "✓ pymxs (3ds Max Python)" || echo "⚠️  pymxs not available (run in 3ds Max or use 3ds Max Python)"
    echo "✅ Core dependencies verified"

# ============================================================================
# Linting & Code Quality
# ============================================================================

# Run ruff check on src/ and tests/
@lint:
    echo "🔍 Running ruff lint check..."
    python -m ruff check src/ tests/
    echo "✅ Lint check passed"

# Auto-fix ruff errors
@lint-fix:
    echo "🔧 Auto-fixing ruff errors..."
    python -m ruff check --fix src/ tests/
    echo "✅ Lint errors fixed"

# Run all lint checks
@lint-all: lint
    echo "✅ All lint checks passed"

# Pre-commit gate: auto-fix, format, lint, quick tests.
# Run this before every commit/push to avoid CI failures.
# Usage: vx just prek   or   just prek
@prek:
    echo "🔧 Auto-fixing ruff errors..."
    python -m ruff check --fix src/ tests/
    echo "🎨 Formatting with ruff..."
    python -m ruff format src/ tests/
    echo "🔍 Running all lint checks..."
    python -m ruff check src/ tests/
    echo "🧪 Running quick tests..."
    python -m pytest tests/ -x -q --ignore=tests/test_e2e_3dsmax_standalone.py
    echo "✅ prek passed — safe to commit"

# ============================================================================
# Testing
# ============================================================================

# Run basic import tests
@test-imports:
    echo "🧪 Running import tests..."
    python -m pytest tests/test_basic_imports.py -v 2>/dev/null || echo "⚠️  test_basic_imports.py not found"
    echo "✅ Import tests passed"

# Run all quick tests (no 3ds Max required)
@test-quick: test-imports
    echo "🧪 Running quick tests..."
    python -m pytest tests/ -x -q
    echo "✅ Quick tests passed"

# Run tests with coverage
@test-coverage:
    echo "🧪 Running tests with coverage..."
    python -m pytest --cov=dcc_mcp_3dsmax --cov-report=term-missing tests/
    echo "✅ Tests complete with coverage report"

# Run specific test file
@test file="tests/test_basic_imports.py":
    python -m pytest {{file}} -v

# ============================================================================
# Development Workflow
# ============================================================================

# Setup development environment (install + verify)
@setup: install-dev verify-deps
    echo "✅ Development environment ready"

# Check code before commit (lint + quick tests)
@check: lint test-quick
    echo "✅ All checks passed - ready to commit"

# Full CI simulation (lint + tests)
@ci: lint-all test-coverage
    echo "✅ CI simulation complete"

# Clean build artifacts
@clean:
    echo "🧹 Cleaning build artifacts..."
    rm -rf build/ dist/ *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    echo "✅ Cleaned"

# Full clean (including test cache)
@clean-all: clean
    echo "🧹 Deep cleaning..."
    rm -rf .pytest_cache .ruff_cache .coverage htmlcov/
    rm -rf tests/.pytest_cache
    echo "✅ Fully cleaned"

# ============================================================================
# Help & Info
# ============================================================================

# Show Python and dependency versions
@versions:
    echo "📦 Environment Information:"
    python --version
    echo ""
    echo "Key Packages:"
    python -m pip show dcc-mcp-3dsmax | grep Version
    python -m pip show dcc-mcp-core | grep Version
    python -m pip show pytest | grep Version
    python -m pip show ruff | grep Version

# Show dependency tree
@deps-tree:
    echo "📦 Dependency tree (core packages):"
    python -m pip show dcc-mcp-3dsmax -f 2>/dev/null | grep "Location\|Requires" || echo "dcc-mcp-3dsmax not installed"
    echo ""
    python -m pip show dcc-mcp-core -f | grep "Location\|Requires"

# ============================================================================
# CI/CD Utilities
# ============================================================================

# Install CI dependencies (for GitHub Actions)
@install-ci: install-dev
    echo "✅ CI dependencies ready"

# Run CI checks locally
@run-ci: clean lint-all test-quick
    echo "✅ Local CI checks passed"

# ============================================================================
# Troubleshooting
# ============================================================================

# Diagnose dependency issues
@diagnose:
    echo "🔍 Diagnosing environment..."
    echo ""
    echo "Python version:"
    python --version
    echo ""
    echo "Pip version:"
    python -m pip --version
    echo ""
    echo "Installed packages (key ones):"
    python -m pip list | grep -E "dcc-mcp|pytest|ruff"
    echo ""
    echo "Trying imports:"
    python -c "from dcc_mcp_3dsmax import start_server; print('✓ dcc_mcp_3dsmax imports OK')" 2>&1 || echo "✗ dcc_mcp_3dsmax import failed"
    python -c "from dcc_mcp_core import create_skill_server; print('✓ dcc_mcp_core imports OK')" 2>&1 || echo "✗ dcc_mcp_core import failed"
    echo ""
    echo "✅ Diagnostic complete"

# Reinstall all dependencies from scratch
@reinstall-all: clean-all
    echo "🔧 Removing pip cache..."
    python -m pip cache purge
    echo "🔧 Reinstalling all dependencies..."
    just install-all
    just verify-deps
    echo "✅ Full reinstall complete"

# Fix common dependency issues
@fix-deps:
    echo "🔧 Attempting to fix dependency issues..."
    echo "  - Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel
    echo "  - Installing core dependencies..."
    python -m pip install -e .
    echo "  - Installing dev dependencies..."
    python -m pip install -e ".[dev]"
    echo "✅ Dependency issues fixed"

# ============================================================================
# 3ds Max Local Development
# ============================================================================

# 3ds Max version for local dev (override: just max-version=2025 max-link)
max-version := env("MAX_VERSION", "2025")

# Detect 3ds Max scripts directory (platform-aware)
_3dsmax-scripts-dir := if os() == "windows" {
    # 3ds Max uses ADSK_3DSMAX_<version> environment variable or default path
    $maxScripts = env("ADSK_3DSMAX_" + replace(max-version, ".", "_"), "")
    if $maxScripts != "" {
        $maxScripts + "\\scripts"
    } else {
        env("APPDATA", "") + "\\Autodesk\\3dsMax\\" + max-version + "\\scripts"
    }
} else {
    # macOS/Linux (via Wine or native)
    env("HOME", "") + "/.wine/drive_c/Program Files/Autodesk/3ds Max " + max-version + "/scripts"
}

# Create symlinks from source tree into 3ds Max's scripts directory for live development.
# After running this, 3ds Max will use your local source code directly.
@max-link:
    #!/usr/bin/env bash
    set -euo pipefail
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." 2>/dev/null && pwd || pwd)"
    if [ -f "justfile" ]; then PROJECT_ROOT="$(pwd)"; fi

    SCRIPTS_DIR="{{ _3dsmax-scripts-dir }}"
    TARGET="$SCRIPTS_DIR\dcc_mcp_3dsmax"

    echo "🔗 Setting up 3ds Max dev symlinks (3ds Max {{ max-version }})..."
    echo "   Project   : $PROJECT_ROOT"
    echo "   Scripts   : $SCRIPTS_DIR"
    echo ""

    mkdir -p "$SCRIPTS_DIR"

    if [ -L "$TARGET" ]; then
        rm "$TARGET"
        echo "   Removed old symlink"
    elif [ -d "$TARGET" ]; then
        echo "   ⚠️  $TARGET is a real directory (not a symlink)."
        echo "   Remove it manually if you want to use dev symlinks."
        exit 1
    fi;

    if [ "$(uname -s)" = "MINGW"* ] || [ "$(uname -s)" = "MSYS"* ] || [ -n "${WINDIR:-}" ]; then
        cmd //c "mklink /D \"$(cygpath -w "$TARGET")\" \"$(cygpath -w "$PROJECT_ROOT/src/dcc_mcp_3dsmax")\"" 2>/dev/null || \
            { echo "   ⚠️  Symlink failed, copying instead..."; cp -r "$PROJECT_ROOT/src/dcc_mcp_3dsmax" "$TARGET"; }
    else
        ln -sf "$PROJECT_ROOT/src/dcc_mcp_3dsmax" "$TARGET"
    fi;

    echo ""
    echo "   ✅ Symlink created:"
    echo "      $TARGET → $PROJECT_ROOT/src/dcc_mcp_3dsmax (live source)"
    echo ""
    echo "   Next: start 3ds Max {{ max-version }} and run in MAXScript Listener:"
    echo "      python.ExecuteFile \"$TARGET/__init__.py\""

# Windows version: Create symlinks using PowerShell (for native Windows without Git Bash)
@max-link-win:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/max-link-win.ps1 -MaxVersion {{ max-version }}

# Windows: build dcc-mcp-core with **this 3ds Max's Python**, then symlink both
# `dcc_mcp_core` (from core's `python/dcc_mcp_core`) and `dcc_mcp_3dsmax` (from `src/dcc_mcp_3dsmax`)
# into 3ds Max's scripts directory. Then start 3ds Max for debugging.
#
# After run, use MCP URL printed below; see docs for Cursor + debugpy setup.
# Default core repo: sibling directory `../dcc-mcp-core` or env `DCC_MCP_CORE_REPO`.
#
#   just max-dev-build-link-core-win
#   just max-dev-debug-win
#   just max-version=2024 max-dev-debug-win
@max-dev-build-link-core-win:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/max-dev-build-link-core-win.ps1 -MaxVersion {{ max-version }}

@max-dev-debug-win:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/max-dev-build-link-core-win.ps1 -MaxVersion {{ max-version }} -LaunchMax

# Windows: only refresh symlinks (skip maturin develop) after you already built core.
@max-dev-relink-core-win:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/max-dev-build-link-core-win.ps1 -MaxVersion {{ max-version }} -SkipBuild

# Remove dev symlinks
@max-unlink:
    #!/usr/bin/env bash
    set -euo pipefail
    SCRIPTS_DIR="{{ _3dsmax-scripts-dir }}"
    TARGET="$SCRIPTS_DIR\dcc_mcp_3dsmax"

    echo "🧹 Removing 3ds Max dev symlinks..."

    if [ -d "$TARGET" ]; then
        rm -rf "$TARGET"
        echo "   Removed $TARGET"
    fi;

    echo "   ✅ Dev symlinks cleaned up"

# Windows version: Remove dev symlinks using PowerShell
@max-unlink-win:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/max-unlink-win.ps1

# Show current 3ds Max dev link status
@max-status:
    #!/usr/bin/env bash
    SCRIPTS_DIR="{{ _3dsmax-scripts-dir }}"
    TARGET="$SCRIPTS_DIR\dcc_mcp_3dsmax"

    echo "📋 3ds Max dev link status:"
    echo "   Scripts dir: $SCRIPTS_DIR"
    echo ""

    if [ -L "$TARGET" ]; then
        REAL=$(readlink "$TARGET" 2>/dev/null || echo "?")
        echo "   ✅ dcc_mcp_3dsmax → $REAL (symlink)"
    elif [ -d "$TARGET" ]; then
        echo "   ⚠️  dcc_mcp_3dsmax exists (copied, not linked)"
    else
        echo "   ❌ dcc_mcp_3dsmax not found"
    fi

# Windows version: Show 3ds Max dev link status using PowerShell
@max-status-win:
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/max-status-win.ps1

# Start 3ds Max with dev environment (Unix/macOS - requires Wine or native)
@max-start:
    echo "🚀 Starting 3ds Max {{ max-version }}..."
    echo "   Note: On Windows, use 'just max-dev-debug-win' instead"
    echo "   On Unix: wine 'C:\Program Files\Autodesk\3ds Max {{ max-version }}\3dsmax.exe'" || echo "❌ 3ds Max not found"

# Full local dev setup: link + install core + verify
max-dev: max-link verify-deps
    @echo ""
    @echo "📋 Dev environment linked. Now start 3ds Max:"
    @echo "   Windows: just max-dev-debug-win"
    @echo "   Or manually: start 3ds Max {{ max-version }} and run in MAXScript Listener:"
    @echo "      python.ExecuteFile \"%APPDATA%\\Autodesk\\3dsMax\\{{ max-version }}\\scripts\\dcc_mcp_3dsmax\\__init__.py\""
    @echo ""
    @echo "   Verify with:"
    @echo "     just max-status       # Unix/macOS"
    @echo "     just max-status-win   # Windows"
