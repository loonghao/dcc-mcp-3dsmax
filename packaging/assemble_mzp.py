#!/usr/bin/env python3
"""Assemble a drag-and-drop 3ds Max MZP installer for dcc-mcp-3dsmax.

The output is a ZIP-compatible ``.mzp`` archive with an MZP control file
(``mzp.run``) at the archive root. The control file runs ``install.ms`` when
users run the package or drag it into the viewport.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Tuple

PACKAGE_NAME = "dcc-mcp-3dsmax"
PY_PACKAGE_NAME = "dcc_mcp_3dsmax"
CORE_PACKAGE_NAME = "dcc_mcp_core"
SERVER_PACKAGE_NAME = "dcc_mcp_server"
TARGET_PLATFORM = "win64"


def resolve_core_version(project_root: Path) -> str:
    """Resolve the latest PyPI dcc-mcp-core version satisfying pyproject."""
    return resolve_dependency_version(project_root, "dcc-mcp-core")


def resolve_server_version(project_root: Path) -> str:
    """Resolve the latest PyPI dcc-mcp-server version satisfying pyproject."""
    return resolve_dependency_version(project_root, "dcc-mcp-server")


def resolve_dependency_version(project_root: Path, distribution: str) -> str:
    """Resolve the latest PyPI version satisfying a pyproject lower bound."""
    content = (project_root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(rf"{re.escape(distribution)}>=(\d+\.\d+\.\d+)", content)
    if not match:
        raise RuntimeError(f"Cannot find {distribution} minimum version in pyproject.toml")
    minimum = match.group(1)

    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{distribution}/json", timeout=15) as resp:
            data = json.loads(resp.read())
        latest = data.get("info", {}).get("version", "")
        if latest and _version_gte(latest, minimum):
            print(f"Resolved {distribution} {latest} from PyPI")
            return latest
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not query latest {distribution} ({exc}); using {minimum}")

    return minimum


def _version_gte(version: str, minimum: str) -> bool:
    return [int(part) for part in version.split(".")] >= [int(part) for part in minimum.split(".")]


def _core_wheel_patterns() -> List[Tuple[str, str]]:
    return [
        ("cp37-cp37m-win_amd64", "Python 3.7 / 3ds Max 2022"),
        ("cp38-abi3-win_amd64", "Python 3.8+ / modern 3ds Max"),
    ]


def download_core_wheels(version: str, dest: Path) -> List[Path]:
    """Download Windows dcc-mcp-core wheels needed by the offline installer."""
    pypi_url = f"https://pypi.org/pypi/dcc-mcp-core/{version}/json"
    print(f"Querying {pypi_url}")
    with urllib.request.urlopen(pypi_url, timeout=30) as resp:
        data = json.loads(resp.read())

    files = data.get("releases", {}).get(version, []) or data.get("urls", [])
    wheel_map = {item["filename"]: item["url"] for item in files if item.get("packagetype") == "bdist_wheel"}

    downloaded: List[Path] = []
    for pattern, label in _core_wheel_patterns():
        matches = [filename for filename in wheel_map if pattern in filename]
        if not matches:
            print(f"Warning: no dcc-mcp-core wheel found for {label} ({pattern})")
            continue
        filename = matches[0]
        target = dest / filename
        if not target.exists():
            print(f"Downloading {filename}")
            urllib.request.urlretrieve(wheel_map[filename], str(target))
        downloaded.append(target)

    if not downloaded:
        raise RuntimeError(f"No Windows dcc-mcp-core wheels found for version {version}")
    return downloaded


def download_server_wheel(version: str, dest: Path) -> Path:
    """Download the Windows dcc-mcp-server wheel needed by the sidecar installer."""
    pypi_url = f"https://pypi.org/pypi/dcc-mcp-server/{version}/json"
    print(f"Querying {pypi_url}")
    with urllib.request.urlopen(pypi_url, timeout=30) as resp:
        data = json.loads(resp.read())

    files = data.get("releases", {}).get(version, []) or data.get("urls", [])
    wheel_map = {item["filename"]: item["url"] for item in files if item.get("packagetype") == "bdist_wheel"}
    matches = [filename for filename in wheel_map if filename.endswith("win_amd64.whl")]
    if not matches:
        raise RuntimeError(f"No Windows dcc-mcp-server wheel found for version {version}")

    filename = matches[0]
    target = dest / filename
    if not target.exists():
        print(f"Downloading {filename}")
        urllib.request.urlretrieve(wheel_map[filename], str(target))
    return target


def extract_wheel(wheel_path: Path, dest: Path, *, extensions_only: bool = False) -> None:
    """Extract package files from a wheel without importing platform binaries."""
    with zipfile.ZipFile(str(wheel_path)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            parts = Path(info.filename).parts
            if any(part.endswith(".dist-info") for part in parts):
                continue
            if extensions_only and Path(info.filename).suffix.lower() not in {".pyd", ".dll"}:
                continue
            relative_path = Path(info.filename)
            if len(parts) >= 3 and parts[0].endswith(".data") and parts[1] == "scripts":
                relative_path = Path("scripts", *parts[2:])
            elif any(part.endswith(".data") for part in parts):
                continue
            out = dest / relative_path
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, out.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def copy_package(project_root: Path, dest: Path) -> None:
    src = project_root / "src" / PY_PACKAGE_NAME
    target = dest / PY_PACKAGE_NAME
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))


def write_startup_template(package_root: Path) -> None:
    startup = package_root / "startup" / "dcc_mcp_3dsmax_startup.ms"
    startup.parent.mkdir(parents=True, exist_ok=True)
    startup.write_text(
        """-- Auto-generated by dcc-mcp-3dsmax MZP installer.
-- Adds the installed Python packages to sys.path and installs the DCC MCP menu.
(
    fn _dccMcpNormalizePath value =
    (
        substituteString value "\\\\" "/"
    )

    local userScripts = _dccMcpNormalizePath (getDir #userScripts)
    local installRoot = _dccMcpNormalizePath (userScripts + "/dcc_mcp_3dsmax")
    local uninstallMarker = _dccMcpNormalizePath (userScripts + "/dcc_mcp_3dsmax_uninstall_pending")
    local legacyUninstallMarker = _dccMcpNormalizePath (userScripts + "/dcc_mcp_3dsmax/dcc_mcp_3dsmax_uninstall_pending")
    local startupScript = _dccMcpNormalizePath (getDir #userStartupScripts + "/dcc_mcp_3dsmax_startup.ms")
    local py = ""
    py += "from pathlib import Path\\n"
    py += "import os, shutil, sys\\n"
    py += "root = Path(r'''" + installRoot + "''')\\n"
    py += "uninstall_marker = Path(r'''" + uninstallMarker + "''')\\n"
    py += "legacy_uninstall_marker = Path(r'''" + legacyUninstallMarker + "''')\\n"
    py += "uninstall_markers = [uninstall_marker, legacy_uninstall_marker]\\n"
    py += "startup_script = Path(r'''" + startupScript + "''')\\n"
    py += "def _split_paths(raw):\\n"
    py += "    if not raw:\\n"
    py += "        return []\\n"
    py += "    return [Path(part.strip()).expanduser() for part in raw.split(os.pathsep) if part.strip()]\\n"
    py += "def _candidate_python_dirs(base):\\n"
    py += "    return [base / ('python37' if sys.version_info < (3, 8) else 'python'), base / 'python', base / 'src', base]\\n"
    py += "def _existing(paths):\\n"
    py += "    return [path for path in paths if path.exists()]\\n"
    py += "def _prepend(paths):\\n"
    py += "    for path in reversed(_existing(paths)):\\n"
    py += "        text = str(path)\\n"
    py += "        if text not in sys.path:\\n"
    py += "            sys.path.insert(0, text)\\n"
    py += "def _env_python_paths():\\n"
    py += "    paths = []\\n"
    py += "    paths.extend(_split_paths(os.environ.get('DCC_MCP_3DSMAX_BOOTSTRAP_PATHS')))\\n"
    py += "    paths.extend(_split_paths(os.environ.get('DCC_MCP_PYTHONPATHS')))\\n"
    py += "    for name in ('DCC_MCP_3DSMAX_ROOT', 'DCC_MCP_CORE_ROOT', 'DCC_MCP_SERVER_ROOT'):\\n"
    py += "        value = os.environ.get(name)\\n"
    py += "        if value:\\n"
    py += "            paths.extend(_candidate_python_dirs(Path(value).expanduser()))\\n"
    py += "    return paths\\n"
    py += "def _installed_root():\\n"
    py += "    current_file = root / 'current.txt'\\n"
    py += "    if current_file.exists():\\n"
    py += "        current = current_file.read_text(encoding='utf-8').strip()\\n"
    py += "        candidate = root / 'versions' / current\\n"
    py += "        if current and candidate.exists():\\n"
    py += "            return candidate\\n"
    py += "    return root\\n"
    py += "def _uninstall_pending():\\n"
    py += "    return any(marker.exists() for marker in uninstall_markers)\\n"
    py += "def _clear_uninstall_markers():\\n"
    py += "    for marker in uninstall_markers:\\n"
    py += "        try:\\n"
    py += "            if marker.exists():\\n"
    py += "                marker.unlink()\\n"
    py += "        except OSError:\\n"
    py += "            pass\\n"
    py += "def _safe_remove_tree(path):\\n"
    py += "    if not path.exists():\\n"
    py += "        return {'success': True, 'status': 'skipped'}\\n"
    py += "    if path.is_file() or path.is_symlink():\\n"
    py += "        path.unlink()\\n"
    py += "        return {'success': True, 'status': 'removed'}\\n"
    py += "    pkg = _installed_root() / ('python37' if sys.version_info < (3, 8) else 'python')\\n"
    py += "    if pkg.exists() and str(pkg) not in sys.path:\\n"
    py += "        sys.path.insert(0, str(pkg))\\n"
    py += "    try:\\n"
    py += "        from dcc_mcp_core.install_lifecycle import safe_remove_tree\\n"
    py += "    except Exception:\\n"
    py += "        shutil.rmtree(path)\\n"
    py += "        return {'success': True, 'status': 'removed'}\\n"
    py += "    result = safe_remove_tree(path)\\n"
    py += "    if not result.get('success') and not result.get('requires_restart'):\\n"
    py += "        raise RuntimeError(result.get('message') or result.get('status') or 'remove failed')\\n"
    py += "    return result\\n"
    py += "def _cleanup_obsolete_payloads(active_root):\\n"
    py += "    if active_root == root or not root.exists():\\n"
    py += "        return\\n"
    py += "    active_name = active_root.name\\n"
    py += "    obsolete = []\\n"
    py += "    versions_dir = root / 'versions'\\n"
    py += "    if versions_dir.exists():\\n"
    py += "        obsolete.extend(path for path in versions_dir.iterdir() if path.name != active_name and not path.name.endswith('.installing'))\\n"
    py += "    for path in root.iterdir():\\n"
    py += "        if path.name in ('versions', 'current.txt'):\\n"
    py += "            continue\\n"
    py += "        if path in uninstall_markers:\\n"
    py += "            continue\\n"
    py += "        obsolete.append(path)\\n"
    py += "    for path in obsolete:\\n"
    py += "        try:\\n"
    py += "            result = _safe_remove_tree(path)\\n"
    py += "            if result.get('requires_restart'):\\n"
    py += "                print('Old dcc-mcp-3dsmax payload cleanup requires restart:', path, result.get('message'))\\n"
    py += "        except Exception as exc:\\n"
    py += "            print('Failed to cleanup old dcc-mcp-3dsmax payload:', path, exc)\\n"
    py += "if _uninstall_pending():\\n"
    py += "    cleanup_done = True\\n"
    py += "    if root.exists():\\n"
    py += "        result = _safe_remove_tree(root)\\n"
    py += "        if result.get('requires_restart'):\\n"
    py += "            cleanup_done = False\\n"
    py += "            print('Deferred dcc-mcp-3dsmax uninstall still requires restart:', result.get('message'))\\n"
    py += "    if cleanup_done and startup_script.exists():\\n"
    py += "        startup_script.unlink()\\n"
    py += "    if cleanup_done:\\n"
    py += "        _clear_uninstall_markers()\\n"
    py += "        print('Completed deferred dcc-mcp-3dsmax uninstall')\\n"
    py += "else:\\n"
    py += "    env_paths = _env_python_paths()\\n"
    py += "    _prepend(env_paths)\\n"
    py += "    install_payload = _installed_root()\\n"
    py += "    _cleanup_obsolete_payloads(install_payload)\\n"
    py += "    pkg = install_payload / ('python37' if sys.version_info < (3, 8) else 'python')\\n"
    py += "    if str(pkg) not in sys.path:\\n"
    py += "        if env_paths:\\n"
    py += "            sys.path.append(str(pkg))\\n"
    py += "        else:\\n"
    py += "            sys.path.insert(0, str(pkg))\\n"
    py += "    os.environ.setdefault('DCC_MCP_SERVER_ROOT', str(pkg))\\n"
    py += "    import dcc_mcp_3dsmax\\n"
    py += "    dcc_mcp_3dsmax.install_menu()\\n"
    py += "    dcc_mcp_3dsmax.install_shutdown_callback()\\n"
    py += "    dcc_mcp_3dsmax.start_sidecar_bridge()\\n"
    py += "    print('dcc-mcp-3dsmax sidecar ready:', pkg)\\n"
    python.Execute py
)
""",
        encoding="utf-8",
    )


def write_mzp_run(package_root: Path, version: str) -> None:
    (package_root / "mzp.run").write_text(
        f"""name "dcc-mcp-3dsmax"
description "dcc-mcp-3dsmax {version} drag-and-drop installer"
version 1
run "install.ms"
drop "install.ms"
clear temp on MAX exit
""",
        encoding="utf-8",
    )


def write_install_script(package_root: Path, version: str) -> None:
    (package_root / "install.ms").write_text(
        f"""-- dcc-mcp-3dsmax {version} drag-and-drop installer.
(
    fn _dccMcpNormalizePath value =
    (
        substituteString value "\\\\" "/"
    )

    local sourceRoot = _dccMcpNormalizePath (getFilenamePath (getSourceFileName()))
    local userScripts = _dccMcpNormalizePath (getDir #userScripts)
    local userStartupScripts = _dccMcpNormalizePath (getDir #userStartupScripts)
    fn _dccMcpInstall =
    (
        local py = ""
        py += "from pathlib import Path\\n"
        py += "import os, shutil, sys, time, uuid\\n"
        py += "source = Path(r'''" + sourceRoot + "''')\\n"
        py += "install_dir = Path(r'''" + userScripts + "''') / 'dcc_mcp_3dsmax'\\n"
        py += "versions_dir = install_dir / 'versions'\\n"
        py += "current_file = install_dir / 'current.txt'\\n"
        py += "uninstall_marker = Path(r'''" + userScripts + "''') / 'dcc_mcp_3dsmax_uninstall_pending'\\n"
        py += "legacy_uninstall_marker = install_dir / 'dcc_mcp_3dsmax_uninstall_pending'\\n"
        py += "uninstall_markers = [uninstall_marker, legacy_uninstall_marker]\\n"
        py += "startup_dir = Path(r'''" + userStartupScripts + "''')\\n"
        py += "startup_script = startup_dir / 'dcc_mcp_3dsmax_startup.ms'\\n"
        py += "version_name = '{version}'\\n"
        py += "def _pkg(root):\\n"
        py += "    return root / ('python37' if sys.version_info < (3, 8) else 'python')\\n"
        py += "def _clear_path(path, allow_restart=False):\\n"
        py += "    if not path.exists():\\n"
        py += "        return {{'success': True, 'status': 'skipped'}}\\n"
        py += "    if path.is_file() or path.is_symlink():\\n"
        py += "        path.unlink()\\n"
        py += "        return {{'success': True, 'status': 'removed'}}\\n"
        py += "    try:\\n"
        py += "        from dcc_mcp_core.install_lifecycle import safe_remove_tree\\n"
        py += "    except Exception:\\n"
        py += "        shutil.rmtree(path)\\n"
        py += "        return {{'success': True, 'status': 'removed'}}\\n"
        py += "    result = safe_remove_tree(path)\\n"
        py += "    if result.get('requires_restart') and allow_restart:\\n"
        py += "        return result\\n"
        py += "    if not result.get('success'):\\n"
        py += "        raise RuntimeError(result.get('message') or result.get('status') or 'remove failed')\\n"
        py += "    return result\\n"
        py += "def _version_key():\\n"
        py += "    safe = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in version_name) or 'dev'\\n"
        py += "    return safe + '_' + time.strftime('%Y%m%d%H%M%S') + '_' + uuid.uuid4().hex[:8]\\n"
        py += "def _active_root():\\n"
        py += "    if current_file.exists():\\n"
        py += "        current = current_file.read_text(encoding='utf-8').strip()\\n"
        py += "        candidate = versions_dir / current\\n"
        py += "        if current and candidate.exists():\\n"
        py += "            return candidate\\n"
        py += "    return install_dir\\n"
        py += "def _copy_payload(target):\\n"
        py += "    shutil.copytree(source / 'payload', target)\\n"
        py += "def _copy_startup(root):\\n"
        py += "    startup_dir.mkdir(parents=True, exist_ok=True)\\n"
        py += "    shutil.copy2(root / 'startup' / 'dcc_mcp_3dsmax_startup.ms', startup_script)\\n"
        py += "def _stop_existing(action):\\n"
        py += "    current_root = _active_root()\\n"
        py += "    if not current_root.exists():\\n"
        py += "        return\\n"
        py += "    pkg = _pkg(current_root)\\n"
        py += "    if pkg.exists() and str(pkg) not in sys.path:\\n"
        py += "        sys.path.insert(0, str(pkg))\\n"
        py += "    try:\\n"
        py += "        import dcc_mcp_3dsmax\\n"
        py += "    except ModuleNotFoundError:\\n"
        py += "        return\\n"
        py += "    try:\\n"
        py += "        dcc_mcp_3dsmax.stop_sidecar_bridge()\\n"
        py += "    except Exception as exc:\\n"
        py += "        raise RuntimeError('Failed to stop dcc-mcp-3dsmax sidecar before ' + action + ': %s' % exc) from exc\\n"
        py += "def _clear_uninstall_markers():\\n"
        py += "    for marker in uninstall_markers:\\n"
        py += "        try:\\n"
        py += "            if marker.exists():\\n"
        py += "                marker.unlink()\\n"
        py += "        except OSError:\\n"
        py += "            pass\\n"
        py += "def _clear_adapter_modules():\\n"
        py += "    for name in list(sys.modules):\\n"
        py += "        if name == 'dcc_mcp_3dsmax' or name.startswith('dcc_mcp_3dsmax.'):\\n"
        py += "            sys.modules.pop(name, None)\\n"
        py += "def _cleanup_obsolete_payloads(active_key):\\n"
        py += "    active_root = versions_dir / active_key\\n"
        py += "    pkg = _pkg(active_root)\\n"
        py += "    if pkg.exists() and str(pkg) not in sys.path:\\n"
        py += "        sys.path.insert(0, str(pkg))\\n"
        py += "    obsolete = []\\n"
        py += "    if versions_dir.exists():\\n"
        py += "        obsolete.extend(path for path in versions_dir.iterdir() if path.name != active_key and not path.name.endswith('.installing'))\\n"
        py += "    if install_dir.exists():\\n"
        py += "        for path in install_dir.iterdir():\\n"
        py += "            if path.name in ('versions', 'current.txt'):\\n"
        py += "                continue\\n"
        py += "            if path in uninstall_markers:\\n"
        py += "                continue\\n"
        py += "            obsolete.append(path)\\n"
        py += "    for path in obsolete:\\n"
        py += "        try:\\n"
        py += "            result = _clear_path(path, allow_restart=True)\\n"
        py += "            if result.get('requires_restart'):\\n"
        py += "                print('Old dcc-mcp-3dsmax payload cleanup requires restart:', path, result.get('message'))\\n"
        py += "        except Exception as exc:\\n"
        py += "            print('Failed to cleanup old dcc-mcp-3dsmax payload:', path, exc)\\n"
        py += "def _activate_runtime(root):\\n"
        py += "    _clear_adapter_modules()\\n"
        py += "    pkg = _pkg(root)\\n"
        py += "    if str(pkg) not in sys.path:\\n"
        py += "        sys.path.insert(0, str(pkg))\\n"
        py += "    os.environ.setdefault('DCC_MCP_SERVER_ROOT', str(pkg))\\n"
        py += "    import dcc_mcp_3dsmax\\n"
        py += "    dcc_mcp_3dsmax.install_menu()\\n"
        py += "    dcc_mcp_3dsmax.install_shutdown_callback()\\n"
        py += "    dcc_mcp_3dsmax.start_sidecar_bridge()\\n"
        py += "_stop_existing('install')\\n"
        py += "_clear_adapter_modules()\\n"
        py += "install_dir.mkdir(parents=True, exist_ok=True)\\n"
        py += "versions_dir.mkdir(parents=True, exist_ok=True)\\n"
        py += "_clear_uninstall_markers()\\n"
        py += "key = _version_key()\\n"
        py += "version_dir = versions_dir / key\\n"
        py += "staging_dir = versions_dir / (key + '.installing')\\n"
        py += "_clear_path(staging_dir)\\n"
        py += "_copy_payload(staging_dir)\\n"
        py += "staging_dir.rename(version_dir)\\n"
        py += "current_file.write_text(key + '\\\\n', encoding='utf-8')\\n"
        py += "_copy_startup(version_dir)\\n"
        py += "_cleanup_obsolete_payloads(key)\\n"
        py += "_activate_runtime(version_dir)\\n"
        py += "print('Installed dcc-mcp-3dsmax', version_name, 'to', version_dir)\\n"
        try
        (
            python.Execute py
            messageBox "dcc-mcp-3dsmax installed and sidecar startup requested." title:"dcc-mcp-3dsmax"
        )
        catch
        (
            messageBox ("dcc-mcp-3dsmax install failed:\\n" + getCurrentException()) title:"dcc-mcp-3dsmax"
        )
    )

    fn _dccMcpUninstall =
    (
        local py = ""
        py += "from pathlib import Path\\n"
        py += "import shutil, sys\\n"
        py += "source = Path(r'''" + sourceRoot + "''')\\n"
        py += "install_dir = Path(r'''" + userScripts + "''') / 'dcc_mcp_3dsmax'\\n"
        py += "versions_dir = install_dir / 'versions'\\n"
        py += "current_file = install_dir / 'current.txt'\\n"
        py += "uninstall_marker = Path(r'''" + userScripts + "''') / 'dcc_mcp_3dsmax_uninstall_pending'\\n"
        py += "legacy_uninstall_marker = install_dir / 'dcc_mcp_3dsmax_uninstall_pending'\\n"
        py += "uninstall_markers = [uninstall_marker, legacy_uninstall_marker]\\n"
        py += "startup_dir = Path(r'''" + userStartupScripts + "''')\\n"
        py += "startup_script = Path(r'''" + userStartupScripts + "''') / 'dcc_mcp_3dsmax_startup.ms'\\n"
        py += "def _active_root():\\n"
        py += "    if current_file.exists():\\n"
        py += "        current = current_file.read_text(encoding='utf-8').strip()\\n"
        py += "        candidate = versions_dir / current\\n"
        py += "        if current and candidate.exists():\\n"
        py += "            return candidate\\n"
        py += "    return install_dir\\n"
        py += "pkg = _active_root() / ('python37' if sys.version_info < (3, 8) else 'python')\\n"
        py += "if str(pkg) not in sys.path:\\n"
        py += "    sys.path.insert(0, str(pkg))\\n"
        py += "try:\\n"
        py += "    import dcc_mcp_3dsmax\\n"
        py += "    dcc_mcp_3dsmax.stop_sidecar_bridge()\\n"
        py += "except ModuleNotFoundError:\\n"
        py += "    pass\\n"
        py += "except Exception as exc:\\n"
        py += "    raise RuntimeError('Failed to stop dcc-mcp-3dsmax sidecar before uninstall: {{}}'.format(exc)) from exc\\n"
        py += "def _clear_adapter_modules():\\n"
        py += "    for name in list(sys.modules):\\n"
        py += "        if name == 'dcc_mcp_3dsmax' or name.startswith('dcc_mcp_3dsmax.'):\\n"
        py += "            sys.modules.pop(name, None)\\n"
        py += "def _clear_uninstall_markers():\\n"
        py += "    for marker in uninstall_markers:\\n"
        py += "        try:\\n"
        py += "            if marker.exists():\\n"
        py += "                marker.unlink()\\n"
        py += "        except OSError:\\n"
        py += "            pass\\n"
        py += "def _clear_path(path):\\n"
        py += "    if path.exists():\\n"
        py += "        if path.is_file() or path.is_symlink():\\n"
        py += "            path.unlink()\\n"
        py += "            return {{'success': True, 'status': 'removed'}}\\n"
        py += "        try:\\n"
        py += "            from dcc_mcp_core.install_lifecycle import safe_remove_tree\\n"
        py += "        except Exception:\\n"
        py += "            shutil.rmtree(path)\\n"
        py += "            return {{'success': True, 'status': 'removed'}}\\n"
        py += "        result = safe_remove_tree(path)\\n"
        py += "        if result.get('requires_restart'):\\n"
        py += "            raise PermissionError(result.get('message') or result.get('recommended_next_action'))\\n"
        py += "        if not result.get('success'):\\n"
        py += "            raise RuntimeError(result.get('message') or result.get('status') or 'remove failed')\\n"
        py += "        return result\\n"
        py += "    return {{'success': True, 'status': 'skipped'}}\\n"
        py += "try:\\n"
        py += "    _clear_adapter_modules()\\n"
        py += "    _clear_path(install_dir)\\n"
        py += "    if startup_script.exists():\\n"
        py += "        startup_script.unlink()\\n"
        py += "    _clear_uninstall_markers()\\n"
        py += "    print('Uninstalled dcc-mcp-3dsmax from', install_dir)\\n"
        py += "except PermissionError as exc:\\n"
        py += "    uninstall_marker.parent.mkdir(parents=True, exist_ok=True)\\n"
        py += "    startup_dir.mkdir(parents=True, exist_ok=True)\\n"
        py += "    uninstall_marker.write_text('pending\\n', encoding='utf-8')\\n"
        py += "    shutil.copy2(source / 'payload' / 'startup' / 'dcc_mcp_3dsmax_startup.ms', startup_script)\\n"
        py += "    print('dcc-mcp-3dsmax uninstall requires a 3ds Max restart; staged cleanup for', install_dir, 'because:', exc)\\n"
        try
        (
            python.Execute py
            messageBox "dcc-mcp-3dsmax uninstall requested. Restart 3ds Max to finish if files were in use." title:"dcc-mcp-3dsmax"
        )
        catch
        (
            messageBox ("dcc-mcp-3dsmax uninstall failed:\\n" + getCurrentException()) title:"dcc-mcp-3dsmax"
        )
    )

    rollout dccMcpInstaller "dcc-mcp-3dsmax" width:280 height:110
    (
        label infoLbl "Choose an action for dcc-mcp-3dsmax:" pos:[20,16]
        button installBtn "Install" width:110 height:28 pos:[20,50]
        button uninstallBtn "Uninstall" width:110 height:28 pos:[145,50]

        on installBtn pressed do
        (
            destroyDialog dccMcpInstaller
            _dccMcpInstall()
        )

        on uninstallBtn pressed do
        (
            destroyDialog dccMcpInstaller
            _dccMcpUninstall()
        )
    )

    createDialog dccMcpInstaller style:#(#style_titlebar, #style_border, #style_sysmenu)
)
""",
        encoding="utf-8",
    )


def assemble(project_root: Path, version: str, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    archive_root = output / f"{PACKAGE_NAME}-{version}-{TARGET_PLATFORM}"
    if archive_root.exists():
        shutil.rmtree(archive_root)
    payload = archive_root / "payload"
    python_dir = payload / "python"
    python37_dir = payload / "python37"
    python_dir.mkdir(parents=True)

    core_version = resolve_core_version(project_root)
    server_version = resolve_server_version(project_root)
    with tempfile.TemporaryDirectory() as tmp:
        wheels = download_core_wheels(core_version, Path(tmp))
        server_wheel = download_server_wheel(server_version, Path(tmp))
        abi3_wheels = [wheel for wheel in wheels if "abi3" in wheel.name]
        cp37_wheels = [wheel for wheel in wheels if "cp37-cp37m" in wheel.name]

        for wheel in abi3_wheels or wheels:
            print(f"Extracting {wheel.name} to python/")
            extract_wheel(wheel, python_dir)

        if cp37_wheels:
            shutil.copytree(python_dir, python37_dir)
            for wheel in cp37_wheels:
                print(f"Extracting {wheel.name} extension files to python37/")
                extract_wheel(wheel, python37_dir, extensions_only=True)

        print(f"Extracting {server_wheel.name} to python/")
        extract_wheel(server_wheel, python_dir)
        if python37_dir.exists():
            print(f"Extracting {server_wheel.name} to python37/")
            extract_wheel(server_wheel, python37_dir)

    copy_package(project_root, python_dir)
    if python37_dir.exists():
        copy_package(project_root, python37_dir)

    readme = project_root / "packaging" / "README.txt"
    if readme.exists():
        shutil.copy2(readme, payload / "README.txt")

    write_startup_template(payload)
    write_mzp_run(archive_root, version)
    write_install_script(archive_root, version)

    mzp_base = output / archive_root.name
    zip_path = shutil.make_archive(str(mzp_base), "zip", root_dir=archive_root)
    mzp_path = Path(zip_path).with_suffix(".mzp")
    if mzp_path.exists():
        mzp_path.unlink()
    Path(zip_path).rename(mzp_path)
    print(f"Created {mzp_path}")
    return mzp_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble dcc-mcp-3dsmax MZP installer")
    parser.add_argument("--version", required=True, help="Package version, for example 0.1.0")
    parser.add_argument("--output", default="dist/mzp", help="Output directory")
    parser.add_argument("--project-root", default=".", help="Project root")
    args = parser.parse_args()

    assemble(Path(args.project_root).resolve(), args.version, Path(args.output).resolve())


if __name__ == "__main__":
    main()
