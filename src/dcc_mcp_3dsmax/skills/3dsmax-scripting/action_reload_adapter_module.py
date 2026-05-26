"""Reload adapter-owned Python modules."""

from __future__ import annotations

import importlib
import sys
import traceback
from typing import Any, Dict

from dcc_mcp_3dsmax.api import max_error


def main(module_name: str) -> Dict[str, Any]:
    """Reload one ``dcc_mcp_3dsmax`` module by name."""
    if not isinstance(module_name, str) or not module_name.strip():
        return max_error("module_name must be a non-empty string")
    module_name = module_name.strip()
    if module_name == "dcc_mcp_3dsmax" or not module_name.startswith("dcc_mcp_3dsmax."):
        return max_error("module_name must identify an adapter-owned dcc_mcp_3dsmax submodule")

    try:
        module = sys.modules.get(module_name)
        if module is None:
            module = importlib.import_module(module_name)
            action = "imported"
        else:
            module = importlib.reload(module)
            action = "reloaded"
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "message": "Adapter module reload failed",
            "data": {
                "module_name": module_name,
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        }

    return {
        "success": True,
        "message": "Adapter module {}".format(action),
        "data": {"module_name": module.__name__, "action": action},
    }
