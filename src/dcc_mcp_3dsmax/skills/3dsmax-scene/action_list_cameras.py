"""List camera nodes in 3ds Max."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._scene_utils import is_camera_node, iter_scene_nodes, node_identity
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """List camera nodes with stable identity data."""
    cameras = [node_identity(node) for node in iter_scene_nodes(get_runtime()) if is_camera_node(node)]
    return {"success": True, "message": "Listed cameras", "data": {"cameras": cameras, "count": len(cameras)}}
