"""Delete 3ds Max nodes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import node_identity, resolve_node_objects
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(node_names: Optional[list] = None, handles: Optional[list] = None) -> Dict[str, Any]:
    """Delete resolved nodes."""
    rt = get_runtime()
    result = resolve_node_objects(rt, node_names=node_names, handles=handles)
    if not result.get("success"):
        return {"success": False, "message": result["message"], "data": result}
    deleted = [node_identity(node) for node in result["objects"]]
    try:
        rt.delete(result["objects"])
    except Exception:
        for node in result["objects"]:
            rt.delete(node)
    return {"success": True, "message": "Deleted nodes", "data": {"nodes": deleted, "count": len(deleted)}}
