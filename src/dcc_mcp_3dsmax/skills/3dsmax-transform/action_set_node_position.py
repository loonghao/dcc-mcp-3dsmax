"""Set a 3ds Max node position."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._scene_utils import node_identity, set_node_position
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(node_name: str, position: Any) -> Dict[str, Any]:
    """Set an existing node to an absolute position."""
    if not isinstance(node_name, str) or not node_name.strip():
        return max_error("node_name must be a non-empty string")

    rt = get_runtime()
    node = rt.getNodeByName(node_name)
    if node is None:
        return max_error("Node not found: {}".format(node_name))

    applied = set_node_position(rt, node, position)
    payload = node_identity(node)
    payload["position"] = applied
    return {
        "success": True,
        "message": "Set position for {}".format(payload["node_name"]),
        "data": payload,
    }
