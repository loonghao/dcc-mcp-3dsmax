"""Tests for the MZP package assembler."""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


def _load_assembler():
    module_path = Path(__file__).resolve().parents[1] / "packaging" / "assemble_mzp.py"
    spec = importlib.util.spec_from_file_location("assemble_mzp", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mzp_run_is_control_file(tmp_path):
    """mzp.run must contain MZP commands, not the installer MaxScript body."""
    assembler = _load_assembler()

    assembler.write_mzp_run(tmp_path, "1.2.3")

    text = (tmp_path / "mzp.run").read_text(encoding="utf-8")
    assert 'name "dcc-mcp-3dsmax"' in text
    assert 'description "dcc-mcp-3dsmax 1.2.3 drag-and-drop installer"' in text
    assert 'run "install.ms"' in text
    assert 'drop "install.ms"' in text
    assert "clear temp on MAX exit" in text
    assert "python.Execute" not in text
    assert "messageBox" not in text


def test_install_script_normalizes_paths_before_embedding_in_python(tmp_path):
    """Generated MaxScript avoids raw Python strings ending in backslashes."""
    assembler = _load_assembler()

    assembler.write_install_script(tmp_path, "1.2.3")

    text = (tmp_path / "install.ms").read_text(encoding="utf-8")
    assert "local sourceRoot = _dccMcpNormalizePath (getFilenamePath (getSourceFileName()))" in text
    assert "local userScripts = _dccMcpNormalizePath (getDir #userScripts)" in text
    assert "local userStartupScripts = _dccMcpNormalizePath (getDir #userStartupScripts)" in text
    assert "source = Path(r'''" in text
    assert "dcc_mcp_3dsmax.install_menu()" in text
    assert "dcc_mcp_3dsmax.install_shutdown_callback()" in text
    assert "button installBtn \"Install\"" in text
    assert "button uninstallBtn \"Uninstall\"" in text
    assert "dcc_mcp_3dsmax.stop_sidecar_bridge()" in text
    assert "Failed to stop dcc-mcp-3dsmax sidecar before uninstall" in text
    assert "dcc-mcp-3dsmax uninstall failed:" in text
    assert "startup_script.unlink()" in text


def test_startup_script_installs_menu_after_adding_package_path(tmp_path):
    """Restarting 3ds Max after MZP install should restore the DCC MCP menu."""
    assembler = _load_assembler()

    assembler.write_startup_template(tmp_path)

    text = (tmp_path / "startup" / "dcc_mcp_3dsmax_startup.ms").read_text(encoding="utf-8")
    assert "local installRoot = _dccMcpNormalizePath" in text
    assert "sys.path.insert(0, str(pkg))" in text
    assert "dcc_mcp_3dsmax.install_menu()" in text
    assert "dcc_mcp_3dsmax.install_shutdown_callback()" in text


def test_extract_wheel_maps_data_scripts_next_to_packages(tmp_path):
    """Wheel .data/scripts entries must land where dcc_mcp_server can find them."""
    assembler = _load_assembler()
    wheel = tmp_path / "dcc_mcp_server-0.17.19-py3-none-win_amd64.whl"
    dest = tmp_path / "python"

    with zipfile.ZipFile(wheel, "w") as zf:
        zf.writestr("dcc_mcp_server/__init__.py", "__version__ = '0.17.19'\n")
        zf.writestr("dcc_mcp_server-0.17.19.data/scripts/dcc-mcp-server.exe", b"binary")
        zf.writestr("dcc_mcp_server-0.17.19.dist-info/METADATA", "Name: dcc-mcp-server\n")

    assembler.extract_wheel(wheel, dest)

    assert (dest / "dcc_mcp_server" / "__init__.py").is_file()
    assert (dest / "scripts" / "dcc-mcp-server.exe").read_bytes() == b"binary"
    assert not (dest / "dcc_mcp_server-0.17.19.data").exists()
    assert not (dest / "dcc_mcp_server-0.17.19.dist-info").exists()
