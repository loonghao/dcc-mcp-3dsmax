"""Move 3ds Max nodes by an offset."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_3dsmax._scene_utils import coerce_vector3, node_identity, point3_to_list
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(
    offset: Any,
    node_names: Optional[List[str]] = None,
    selected: bool = False,
) -> Dict[str, Any]:
    """Move named nodes, selected nodes, or both by a relative offset."""
    rt = get_runtime()
    vector = coerce_vector3(offset, "offset")
    nodes = _resolve_nodes(rt, node_names=node_names, selected=selected)
    if not nodes:
        return max_error("No nodes matched node_names or selected=true")

    moved = []
    delta = rt.Point3(vector[0], vector[1], vector[2])
    for node in nodes:
        current = getattr(node, "pos", rt.Point3(0.0, 0.0, 0.0))
        node.pos = current + delta
        payload = node_identity(node)
        payload["offset"] = vector
        payload["position"] = point3_to_list(getattr(node, "pos", None))
        moved.append(payload)

    return {
        "success": True,
        "message": "Moved {} node(s)".format(len(moved)),
        "data": {
            "nodes": moved,
            "offset": vector,
        },
    }


def _resolve_nodes(rt: Any, node_names: Optional[List[str]], selected: bool) -> List[Any]:
    nodes = []
    seen = set()
    for name in node_names or []:
        node = rt.getNodeByName(name)
        if node is not None:
            _append_unique(nodes, seen, node)
    if selected:
        for node in list(rt.selection):
            _append_unique(nodes, seen, node)
    return nodes


def _append_unique(nodes: List[Any], seen: set, node: Any) -> None:
    key = getattr(node, "handle", None) or id(node)
    if key in seen:
        return
    seen.add(key)
    nodes.append(node)
