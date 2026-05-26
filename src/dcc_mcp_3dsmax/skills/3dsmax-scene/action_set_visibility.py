"""Set visibility for 3ds Max nodes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import node_identity, resolve_node_objects, set_node_visible
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(visible: bool, node_names: Optional[list] = None, handles: Optional[list] = None) -> Dict[str, Any]:
    """Set node visibility."""
    rt = get_runtime()
    result = resolve_node_objects(rt, node_names=node_names, handles=handles)
    if not result.get("success"):
        return {"success": False, "message": result["message"], "data": result}
    for node in result["objects"]:
        set_node_visible(rt, node, bool(visible))
    nodes = [node_identity(node) for node in result["objects"]]
    return {"success": True, "message": "Updated visibility", "data": {"nodes": nodes, "visible": bool(visible)}}
