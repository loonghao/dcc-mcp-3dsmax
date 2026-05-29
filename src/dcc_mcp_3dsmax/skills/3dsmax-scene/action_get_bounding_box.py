"""Get a node bounding box."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import node_bounding_box, resolve_node_object
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(node_name: Optional[str] = None, handle: Optional[int] = None) -> Dict[str, Any]:
    """Return a node bounding box."""
    result, node = resolve_node_object(get_runtime(), node_name=node_name, handle=handle)
    if node is None:
        return {"success": False, "message": result["message"], "data": result}
    return {"success": True, "message": "Retrieved bounding box", "data": node_bounding_box(node)}
