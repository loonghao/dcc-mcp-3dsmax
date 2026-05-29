"""Qt sidecar bridge backed by ``dcc-mcp-core``."""

from __future__ import annotations

import os
from typing import Any, Optional

DEFAULT_QT_BRIDGE_PORT = 0
ENV_QT_BRIDGE_PORT = "DCC_MCP_3DSMAX_QT_BRIDGE_PORT"

_server_handle: Optional[Any] = None
_owned_env_port: Optional[str] = None


def start_qt_bridge(port: Optional[int] = None) -> Any:
    """Start the core Qt dispatcher and return its server handle."""
    global _owned_env_port, _server_handle

    if _server_handle is not None:
        return _server_handle

    env_was_set = ENV_QT_BRIDGE_PORT in os.environ
    resolved_port = int(port if port is not None else os.environ.get(ENV_QT_BRIDGE_PORT, DEFAULT_QT_BRIDGE_PORT))
    from dcc_mcp_core.qt_dispatcher import start_qt_server  # noqa: PLC0415

    _server_handle = start_qt_server(
        port=resolved_port,
        dispatch_handler=_dispatch_payload,
        session_info_provider=_session_info,
    )
    actual_port = int(_server_handle["port"])
    os.environ[ENV_QT_BRIDGE_PORT] = str(actual_port)
    _owned_env_port = None if env_was_set else str(actual_port)
    print("dcc-mcp-3dsmax qt bridge listening on {}".format(_server_handle["url"]))
    return _server_handle


def stop_qt_bridge() -> None:
    """Stop the core Qt dispatcher bridge."""
    global _owned_env_port, _server_handle
    if _server_handle is None:
        return
    close = getattr(_server_handle, "close", None)
    if callable(close):
        close()
    else:
        from dcc_mcp_core.qt_dispatcher import stop_qt_server  # noqa: PLC0415

        stop_qt_server()
    _server_handle = None
    if _owned_env_port is not None and os.environ.get(ENV_QT_BRIDGE_PORT) == _owned_env_port:
        os.environ.pop(ENV_QT_BRIDGE_PORT, None)
    _owned_env_port = None


def qt_bridge_port() -> int:
    """Return the active Qt bridge port, or env/default if not running."""
    if _server_handle is not None:
        return int(_server_handle["port"])
    return int(os.environ.get(ENV_QT_BRIDGE_PORT, DEFAULT_QT_BRIDGE_PORT))


def _session_info() -> dict:
    return {
        "dcc": "3dsmax",
        "bridge_env": ENV_QT_BRIDGE_PORT,
    }


def _dispatch_payload(params: dict) -> dict:
    from dcc_mcp_3dsmax.sidecar._dispatcher import dispatch_payload_dict  # noqa: PLC0415

    return dispatch_payload_dict(params)
