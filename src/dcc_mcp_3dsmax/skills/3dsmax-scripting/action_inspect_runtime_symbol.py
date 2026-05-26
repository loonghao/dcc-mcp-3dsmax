"""Inspect one pymxs runtime symbol."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._scene_utils import runtime_symbol_info
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(name: str) -> Dict[str, Any]:
    """Return shallow metadata for one runtime symbol."""
    if not isinstance(name, str) or not name.strip():
        return max_error("name must be a non-empty runtime symbol name")
    rt = get_runtime()
    info = runtime_symbol_info(rt, name.strip())
    if not info.get("available"):
        return {"success": False, "message": "Runtime symbol not available", "data": info}
    return {"success": True, "message": "Inspected runtime symbol", "data": info}
