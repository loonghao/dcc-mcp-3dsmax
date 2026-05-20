"""JSON-line bridge used by ``dcc-mcp-server sidecar`` over ``qtserver://``."""

from __future__ import annotations

import json
import os
import socketserver
import threading
from typing import Any, Optional

from dcc_mcp_3dsmax.sidecar.bridge import execute_on_main_thread

DEFAULT_QT_BRIDGE_PORT = 0
ENV_QT_BRIDGE_PORT = "DCC_MCP_3DSMAX_QT_BRIDGE_PORT"

_server_instance: Optional[socketserver.ThreadingTCPServer] = None
_server_thread: Optional[threading.Thread] = None
_owned_env_port: Optional[str] = None


class _JsonLineHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            try:
                line = self.rfile.readline()
            except OSError:
                return
            if not line:
                return
            response = _handle_line(line)
            try:
                self.wfile.write(response.encode("utf-8") + b"\n")
                self.wfile.flush()
            except OSError:
                return


class _ThreadingTcpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_qt_bridge(port: Optional[int] = None) -> socketserver.ThreadingTCPServer:
    """Start the JSON-line sidecar bridge and return the TCP server."""
    global _owned_env_port, _server_instance, _server_thread

    if _server_instance is not None:
        return _server_instance

    env_was_set = ENV_QT_BRIDGE_PORT in os.environ
    resolved_port = int(port if port is not None else os.environ.get(ENV_QT_BRIDGE_PORT, DEFAULT_QT_BRIDGE_PORT))
    _server_instance = _ThreadingTcpServer(("127.0.0.1", resolved_port), _JsonLineHandler)
    actual_port = int(_server_instance.server_address[1])
    _server_thread = threading.Thread(
        target=_server_instance.serve_forever,
        daemon=True,
        name="dcc-mcp-3dsmax-qt-bridge",
    )
    _server_thread.start()
    os.environ[ENV_QT_BRIDGE_PORT] = str(actual_port)
    _owned_env_port = None if env_was_set else str(actual_port)
    print("dcc-mcp-3dsmax qt bridge listening on qtserver://127.0.0.1:{}".format(actual_port))
    return _server_instance


def stop_qt_bridge() -> None:
    """Stop the JSON-line sidecar bridge."""
    global _owned_env_port, _server_instance, _server_thread
    if _server_instance is None:
        return
    _server_instance.shutdown()
    _server_instance.server_close()
    _server_instance = None
    _server_thread = None
    if _owned_env_port is not None and os.environ.get(ENV_QT_BRIDGE_PORT) == _owned_env_port:
        os.environ.pop(ENV_QT_BRIDGE_PORT, None)
    _owned_env_port = None


def qt_bridge_port() -> int:
    """Return the active JSON-line bridge port, or env/default if not running."""
    if _server_instance is not None:
        return int(_server_instance.server_address[1])
    return int(os.environ.get(ENV_QT_BRIDGE_PORT, DEFAULT_QT_BRIDGE_PORT))


def _handle_line(raw: bytes) -> str:
    try:
        request = json.loads(raw.decode("utf-8"))
        request_id = str(request.get("id") or "")
        method = request.get("method")
        params = request.get("params") or {}
        if method == "ping":
            return _json({"id": request_id, "result": {"pong": True, "version": "1"}})
        if method != "dispatch":
            return _json(
                {
                    "id": request_id,
                    "error": {
                        "code": "unknown-method",
                        "message": "unknown method {!r}".format(method),
                    },
                }
            )
        if not isinstance(params, dict):
            raise TypeError("params must be an object")
        response = execute_on_main_thread(params)
        result = json.loads(response)
        return _json({"id": request_id, "result": result})
    except Exception as exc:  # noqa: BLE001
        return _json(
            {
                "id": "",
                "error": {
                    "code": "handler-exception",
                    "message": "{}: {}".format(exc.__class__.__name__, exc),
                },
            }
        )


def _json(body: dict[str, Any]) -> str:
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"))
