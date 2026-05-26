"""Get the current 3ds Max selection."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._scene_utils import node_identity
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Return selected nodes."""
    rt = get_runtime()
    try:
        selection = list(rt.selection)
    except Exception:  # noqa: BLE001
        selection = []
    nodes = [node_identity(node) for node in selection]
    return {"success": True, "message": "Retrieved selection", "data": {"nodes": nodes, "count": len(nodes)}}
