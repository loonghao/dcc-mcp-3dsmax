"""Set the active 3ds Max selection."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import node_identity, resolve_node_objects
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(node_names: Optional[list] = None, handles: Optional[list] = None, replace: bool = True) -> Dict[str, Any]:
    """Set or extend the active selection."""
    rt = get_runtime()
    result = resolve_node_objects(rt, node_names=node_names, handles=handles)
    if not result.get("success"):
        return {"success": False, "message": result["message"], "data": result}
    nodes = result["objects"]
    try:
        if replace and hasattr(rt, "clearSelection"):
            rt.clearSelection()
        if not replace and hasattr(rt, "selectMore"):
            for node in nodes:
                rt.selectMore(node)
        elif hasattr(rt, "select"):
            rt.select(nodes)
        else:
            existing = [] if replace else list(getattr(rt, "selection", []) or [])
            rt.selection = existing + [node for node in nodes if node not in existing]
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "message": "Could not set selection", "data": {"error": str(exc)}}
    selected = [node_identity(node) for node in nodes]
    return {"success": True, "message": "Updated selection", "data": {"nodes": selected, "count": len(selected)}}
