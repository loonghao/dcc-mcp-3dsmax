"""Bootstrap helpers for running dcc-mcp-3dsmax inside Autodesk 3ds Max."""

from __future__ import annotations

import atexit
import json
import os
import site
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import Any, Optional

from dcc_mcp_3dsmax.__version__ import __version__
from dcc_mcp_3dsmax._constants import DEFAULT_GATEWAY_PORT
from dcc_mcp_3dsmax.sidecar.bridge import execute_on_main_thread, start_bridge, stop_bridge
from dcc_mcp_3dsmax.sidecar.qt_bridge import qt_bridge_port, start_qt_bridge, stop_qt_bridge

_sidecar_process: Optional[subprocess.Popen] = None
_cleanup_registered = False


def start_embedded_server(port: Optional[int] = None, **kwargs: Any) -> Any:
    """Start the embedded MCP HTTP server inside 3ds Max."""
    from dcc_mcp_3dsmax.server import start_server  # noqa: PLC0415

    resolved_port = int(port if port is not None else os.environ.get("DCC_MCP_3DSMAX_PORT", "0"))
    kwargs.setdefault("gateway_port", DEFAULT_GATEWAY_PORT)
    return start_server(port=resolved_port, **kwargs)


def start_sidecar_bridge(
    bridge_port: Optional[int] = None,
    *,
    register_builtins: bool = True,  # noqa: ARG001 - kept for bootstrap API symmetry.
    include_bundled: bool = True,  # noqa: ARG001 - kept for bootstrap API symmetry.
) -> Any:
    """Start bridges plus the external dcc-mcp-server sidecar process."""
    _register_process_cleanup()
    _install_max_integration()
    bridge = start_bridge(bridge_port)
    qt_bridge = start_qt_bridge()
    process = start_sidecar_server()
    return {"bridge": bridge, "qt_bridge": qt_bridge, "sidecar_process": process}


def start_sidecar_server() -> subprocess.Popen:
    """Start ``dcc-mcp-server.exe sidecar`` for gateway/admin registration."""
    global _sidecar_process

    if _sidecar_process is not None and _sidecar_process.poll() is None:
        return _sidecar_process

    binary = _server_binary_path()
    qt_port = qt_bridge_port()
    pid = os.getpid()
    cmd = [
        str(binary),
        "sidecar",
        "--dcc",
        "3dsmax",
        "--host-rpc",
        "qtserver://127.0.0.1:{}".format(qt_port),
        "--watch-pid",
        str(pid),
        "--adapter-version",
        __version__,
        "--display-name",
        "3ds Max {}".format(_max_version_label()),
        "--gateway-port",
        str(DEFAULT_GATEWAY_PORT),
    ]
    env = dict(os.environ)
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        _sidecar_process = subprocess.Popen(  # noqa: S603 - binary path is resolved locally or explicitly configured.
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
        )
    except Exception:
        raise
    try:
        exit_code = _sidecar_process.wait(timeout=0.75)
    except subprocess.TimeoutExpired:
        exit_code = None
    if exit_code is not None:
        _sidecar_process = None
        raise RuntimeError("dcc-mcp-server sidecar exited during startup with code {}.".format(exit_code))
    print(
        "dcc-mcp-3dsmax sidecar server started pid={} ({})".format(
            _sidecar_process.pid,
            binary,
        )
    )
    print("dcc-mcp-3dsmax MCP gateway available at http://127.0.0.1:{}/mcp".format(DEFAULT_GATEWAY_PORT))
    return _sidecar_process


def stop_sidecar_bridge(timeout: float = 5.0) -> None:
    """Stop the external sidecar process and both localhost bridges."""
    global _sidecar_process

    _stop_embedded_server_if_loaded()

    process = _sidecar_process
    _sidecar_process = None
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=timeout)
        print("dcc-mcp-3dsmax sidecar server stopped pid={}".format(process.pid))

    stop_qt_bridge()
    stop_bridge()


def _stop_embedded_server_if_loaded() -> None:
    server_module = sys.modules.get("dcc_mcp_3dsmax.server")
    if server_module is None:
        return
    stop = getattr(server_module, "stop_server", None)
    if callable(stop):
        stop()


def start_embedded_sidecar_bridge(
    bridge_port: Optional[int] = None,
    *,
    register_builtins: bool = True,
    include_bundled: bool = True,
) -> Any:
    """Start the agent-callable embedded MCP runtime with main-thread execution."""
    from dcc_mcp_core import HostExecutionBridge  # noqa: PLC0415

    from dcc_mcp_3dsmax.server import start_server  # noqa: PLC0415

    bridge = start_bridge(bridge_port)
    execution_bridge = HostExecutionBridge(
        runner=_run_skill_script_via_bridge,
        default_thread_affinity="main",
    )
    server = start_server(
        port=int(os.environ.get("DCC_MCP_3DSMAX_PORT", "0")),
        register_builtins=register_builtins,
        include_bundled=include_bundled,
        gateway_port=DEFAULT_GATEWAY_PORT,
        execution_bridge=execution_bridge,
    )
    print("dcc-mcp-3dsmax MCP gateway available at http://127.0.0.1:{}/mcp".format(DEFAULT_GATEWAY_PORT))
    return {"bridge": bridge, "server": server}


def _run_skill_script_via_bridge(script_path: str, params: dict[str, Any]) -> dict[str, Any]:
    """Route MCP tool execution through the 3ds Max main-thread bridge."""
    raw = execute_on_main_thread({"script_path": script_path, "args": params})
    result = json.loads(raw)
    return result if isinstance(result, dict) else {"success": True, "data": result}


def _server_binary_path() -> Path:
    override = os.environ.get("DCC_MCP_SERVER_BIN")
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path

    binary_name = "dcc-mcp-server.exe" if os.name == "nt" else "dcc-mcp-server"
    candidates = []
    candidates.extend(_bundled_server_binary_candidates(binary_name))
    server_root = os.environ.get("DCC_MCP_SERVER_ROOT")
    if server_root:
        root = Path(server_root).expanduser()
        candidates.extend(
            [
                root / binary_name,
                root / "bin" / binary_name,
                root / "scripts" / binary_name,
                root / "Scripts" / binary_name,
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    try:
        from dcc_mcp_server import binary_path  # noqa: PLC0415

        candidate = Path(binary_path())
        if candidate.is_file():
            return candidate
    except Exception:  # noqa: BLE001
        pass

    fallback_candidates = [
        Path(sysconfig.get_path("scripts") or "") / binary_name,
        Path(site.USER_BASE) / ("Scripts" if os.name == "nt" else "bin") / binary_name,
    ]
    try:
        user_site = Path(site.getusersitepackages())
        fallback_candidates.append(user_site.parent / ("Scripts" if os.name == "nt" else "bin") / binary_name)
    except Exception:  # noqa: BLE001
        pass
    for candidate in fallback_candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "dcc-mcp-server binary not found. Set DCC_MCP_SERVER_BIN to an explicit executable "
        "or install a payload that includes dcc-mcp-server."
    )


def _bundled_server_binary_candidates(binary_name: str) -> list[Path]:
    try:
        package_root = Path(__file__).resolve().parent.parent
    except OSError:
        return []
    return [
        package_root / "scripts" / binary_name,
        package_root / "Scripts" / binary_name,
        package_root / "bin" / binary_name,
        package_root / binary_name,
    ]


def _register_process_cleanup() -> None:
    global _cleanup_registered
    if _cleanup_registered:
        return
    atexit.register(stop_sidecar_bridge)
    _cleanup_registered = True


def _install_max_integration() -> None:
    try:
        from dcc_mcp_3dsmax.menu import install_menu, install_shutdown_callback  # noqa: PLC0415

        install_menu()
        install_shutdown_callback()
    except Exception as exc:  # noqa: BLE001
        print("dcc-mcp-3dsmax Max UI integration skipped: {}".format(exc))


def _max_version_label() -> str:
    try:
        import pymxs  # noqa: PLC0415

        runtime = pymxs.runtime
        version = runtime.maxVersion()
        product_version = _runtime_value(runtime, "productVersion")
        label = _year_label(product_version)
        if label:
            return label

        label = _version_sequence_year(version)
        if label:
            return label

        try:
            major = int(version[0])
        except Exception:  # noqa: BLE001
            return _sanitize_max_version_label(str(version))
        if major >= 10000:
            return str(major // 1000)
        return _sanitize_max_version_label(str(major))
    except Exception:  # noqa: BLE001
        return "unknown"


def _runtime_value(runtime: Any, name: str) -> Any:
    try:
        value = getattr(runtime, name)
        return value() if callable(value) else value
    except Exception:  # noqa: BLE001
        return None


def _version_sequence_year(version: Any) -> Optional[str]:
    for index in (7, 6):
        try:
            label = _year_label(version[index])
        except Exception:  # noqa: BLE001
            continue
        if label:
            return label
    return _year_label(str(version))


def _year_label(value: Any) -> Optional[str]:
    text = _sanitize_max_version_label(str(value)) if value not in (None, "") else ""
    match = None
    if text:
        import re  # noqa: PLC0415

        match = re.search(r"\b(20\d{2})\b", text)
    return match.group(1) if match else None


def _sanitize_max_version_label(value: str) -> str:
    cleaned = value
    for ch in ('"', "'", "\n", "\r", "\t"):
        cleaned = cleaned.replace(ch, " ")
    cleaned = " ".join(cleaned.split())
    return cleaned.strip() or "unknown"


def main() -> Any:
    """Default entry point used by 3ds Max startup scripts."""
    mode = os.environ.get("DCC_MCP_3DSMAX_BOOT_MODE", "runtime").strip().lower()
    if mode == "sidecar":
        return start_sidecar_bridge()

    _register_process_cleanup()
    _install_max_integration()
    if mode in {"server", "embedded-server"}:
        return start_embedded_server()
    if mode in {"runtime", "embedded", "embedded-sidecar", "bridge"}:
        return start_embedded_sidecar_bridge()
    raise ValueError(
        "unsupported DCC_MCP_3DSMAX_BOOT_MODE={!r}; expected runtime, sidecar, or server".format(mode)
    )


if __name__ == "__main__":
    main()
