"""Resolve a 3ds Max node reference."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import resolve_node
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(node_name: Optional[str] = None, handle: Optional[int] = None) -> Dict[str, Any]:
    """Resolve one node by name or object handle."""
    result = resolve_node(get_runtime(), node_name=node_name, handle=handle)
    return {
        "success": bool(result.get("success")),
        "message": str(result.get("message") or "Resolved node reference"),
        "data": result,
    }
