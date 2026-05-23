"""dcc-mcp-3dsmax — 3ds Max plugin for the DCC Model Context Protocol ecosystem.

Embeds a standards-compliant MCP Streamable HTTP server (2025-03-26 spec)
directly inside 3ds Max using dcc-mcp-core.  No external gateway or dcc-mcp-ipc
required.

Quickstart (inside 3ds Max's MAXScript Listener):

    import dcc_mcp_3dsmax
    handle = dcc_mcp_3dsmax.start_server()
    # MCP host connects to http://127.0.0.1:9765/mcp
    handle.shutdown()

Skill authoring helpers (for 3ds Max skills developers):

    from dcc_mcp_3dsmax.api import (
        max_success, max_error, max_from_exception, with_max,
        require_param, validate_node_exists,
    )

    @with_max
    def create_box(width: float = 100.0, height: float = 100.0, depth: float = 100.0) -> dict:
        import pymxs
        rt = pymxs.runtime
        box_obj = rt.Box(width=width, height=height, depth=depth)
        return max_success("Created box", object_name=str(box_obj))
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
from importlib import import_module
from typing import Any

# Import local modules
from dcc_mcp_3dsmax.__version__ import __version__
from dcc_mcp_3dsmax._env import (
    ENV_DISABLE_ARBITRARY_SCRIPT,
    ENV_DISABLE_EXECUTE_MAXSCRIPT,
    ENV_DISABLE_EXECUTE_PYTHON,
    ENV_ENABLE_GATEWAY_FAILOVER,
    resolve_enable_gateway_failover,
    resolve_execute_maxscript_disabled,
    resolve_execute_python_disabled,
)
from dcc_mcp_3dsmax._version_probe import (
    get_3dsmax_version_number,
    get_3dsmax_version_string,
    is_3dsmax_available,
)
from dcc_mcp_3dsmax.api import (
    MissingParamError,
    clear_selection,
    get_param,
    get_runtime,
    get_selection,
    is_max_available,
    max_error,
    max_from_exception,
    max_success,
    max_warning,
    missing_param_error,
    require_any_param,
    require_param,
    select_nodes,
    with_max,
)
from dcc_mcp_3dsmax.capabilities import (
    get_3dsmax_capabilities,
    get_3dsmax_capabilities_dict,
)

_LAZY_EXPORTS = {
    "main": ("dcc_mcp_3dsmax.max_bootstrap", "main"),
    "start_sidecar_bridge": ("dcc_mcp_3dsmax.max_bootstrap", "start_sidecar_bridge"),
    "start_embedded_sidecar_bridge": ("dcc_mcp_3dsmax.max_bootstrap", "start_embedded_sidecar_bridge"),
    "stop_sidecar_bridge": ("dcc_mcp_3dsmax.max_bootstrap", "stop_sidecar_bridge"),
    "install_menu": ("dcc_mcp_3dsmax.menu", "install_menu"),
    "install_shutdown_callback": ("dcc_mcp_3dsmax.menu", "install_shutdown_callback"),
    "MaxMcpServer": ("dcc_mcp_3dsmax.server", "MaxMcpServer"),
    "MaxServerOptions": ("dcc_mcp_3dsmax.server", "MaxServerOptions"),
    "start_server": ("dcc_mcp_3dsmax.server", "start_server"),
    "stop_server": ("dcc_mcp_3dsmax.server", "stop_server"),
    "get_server": ("dcc_mcp_3dsmax.server", "get_server"),
    "prepare_server": ("dcc_mcp_3dsmax.server", "prepare_server"),
    "DEFAULT_GATEWAY_PORT": ("dcc_mcp_3dsmax.server", "DEFAULT_GATEWAY_PORT"),
    "DEFAULT_PORT": ("dcc_mcp_3dsmax.server", "DEFAULT_PORT"),
    "SERVER_NAME": ("dcc_mcp_3dsmax.server", "SERVER_NAME"),
}


def __getattr__(name: str) -> Any:
    """Resolve heavier runtime exports only when callers actually use them."""
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))

__all__ = [
    "__version__",
    # Server
    "MaxMcpServer",
    "MaxServerOptions",
    "start_server",
    "stop_server",
    "get_server",
    "prepare_server",
    "DEFAULT_GATEWAY_PORT",
    "DEFAULT_PORT",
    "SERVER_NAME",
    "main",
    "start_sidecar_bridge",
    "start_embedded_sidecar_bridge",
    "stop_sidecar_bridge",
    "install_menu",
    "install_shutdown_callback",
    # Version
    "get_3dsmax_version_string",
    "get_3dsmax_version_number",
    "is_3dsmax_available",
    # Capabilities
    "get_3dsmax_capabilities",
    "get_3dsmax_capabilities_dict",
    # API helpers
    "max_success",
    "max_error",
    "max_warning",
    "max_from_exception",
    "with_max",
    "require_param",
    "require_any_param",
    "get_param",
    "missing_param_error",
    "MissingParamError",
    "is_max_available",
    "get_runtime",
    "get_selection",
    "clear_selection",
    "select_nodes",
    # Environment
    "ENV_DISABLE_EXECUTE_PYTHON",
    "ENV_DISABLE_EXECUTE_MAXSCRIPT",
    "ENV_DISABLE_ARBITRARY_SCRIPT",
    "ENV_ENABLE_GATEWAY_FAILOVER",
    "resolve_enable_gateway_failover",
    "resolve_execute_python_disabled",
    "resolve_execute_maxscript_disabled",
]
