"""List 3ds Max scene nodes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import is_camera_node, iter_scene_nodes, node_identity
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(name_filter: Optional[str] = None, include_hidden: bool = True, limit: int = 200) -> Dict[str, Any]:
    """List scene nodes with stable identity data."""
    nodes = iter_scene_nodes(get_runtime())
    safe_limit = max(1, min(int(limit or 200), 1000))
    filter_text = (name_filter or "").lower()
    rows = []
    for node in nodes:
        identity = node_identity(node)
        if filter_text and filter_text not in identity["node_name"].lower():
            continue
        if not include_hidden and not identity["visible"]:
            continue
        identity["is_camera"] = is_camera_node(node)
        rows.append(identity)
    return {
        "success": True,
        "message": "Listed scene nodes",
        "data": {"nodes": rows[:safe_limit], "count": min(len(rows), safe_limit), "truncated": len(rows) > safe_limit},
    }
