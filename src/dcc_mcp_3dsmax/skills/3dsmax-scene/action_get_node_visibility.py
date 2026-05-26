"""Get 3ds Max node visibility."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._scene_utils import node_identity, resolve_node_object
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(node_name: Optional[str] = None, handle: Optional[int] = None) -> Dict[str, Any]:
    """Return node visibility."""
    result, node = resolve_node_object(get_runtime(), node_name=node_name, handle=handle)
    if node is None:
        return {"success": False, "message": result["message"], "data": result}
    identity = node_identity(node)
    return {
        "success": True,
        "message": "Retrieved node visibility",
        "data": {"node": identity, "visible": identity["visible"]},
    }
