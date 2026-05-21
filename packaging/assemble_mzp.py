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

    local installRoot = _dccMcpNormalizePath (getDir #userScripts + "/dcc_mcp_3dsmax")
    local py = ""
    py += "from pathlib import Path\\n"
    py += "import sys\\n"
    py += "root = Path(r'''" + installRoot + "''')\\n"
    py += "pkg = root / ('python37' if sys.version_info < (3, 8) else 'python')\\n"
    py += "if str(pkg) not in sys.path:\\n"
    py += "    sys.path.insert(0, str(pkg))\\n"
    py += "import dcc_mcp_3dsmax\\n"
    py += "dcc_mcp_3dsmax.install_menu()\\n"
    py += "dcc_mcp_3dsmax.install_shutdown_callback()\\n"
    py += "print('dcc-mcp-3dsmax path ready:', pkg)\\n"
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
    local py = ""

    py += "from pathlib import Path\\n"
    py += "import shutil, sys\\n"
    py += "source = Path(r'''" + sourceRoot + "''')\\n"
    py += "install_dir = Path(r'''" + userScripts + "''') / 'dcc_mcp_3dsmax'\\n"
    py += "startup_dir = Path(r'''" + userStartupScripts + "''')\\n"
    py += "if install_dir.exists():\\n"
    py += "    shutil.rmtree(install_dir)\\n"
    py += "shutil.copytree(source / 'payload', install_dir)\\n"
    py += "startup_dir.mkdir(parents=True, exist_ok=True)\\n"
    py += "shutil.copy2(install_dir / 'startup' / 'dcc_mcp_3dsmax_startup.ms', startup_dir / 'dcc_mcp_3dsmax_startup.ms')\\n"
    py += "pkg = install_dir / ('python37' if sys.version_info < (3, 8) else 'python')\\n"
    py += "if str(pkg) not in sys.path:\\n"
    py += "    sys.path.insert(0, str(pkg))\\n"
    py += "import dcc_mcp_3dsmax\\n"
    py += "dcc_mcp_3dsmax.install_menu()\\n"
    py += "dcc_mcp_3dsmax.install_shutdown_callback()\\n"
    py += "print('Installed dcc-mcp-3dsmax', dcc_mcp_3dsmax.__version__, 'to', install_dir)\\n"

    python.Execute py
    messageBox "dcc-mcp-3dsmax installed. Restart 3ds Max, then use the DCC MCP menu." title:"dcc-mcp-3dsmax"
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
