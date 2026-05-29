"""Detach selected mesh faces."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import detach_faces, mesh_error, mesh_success, resolve_one, topology_summary
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_name: Optional[str] = None,
    handle: Optional[int] = None,
    face_indices: Optional[list] = None,
    use_current_face_selection: bool = False,
    detach_name: str = "DetachedMesh",
) -> Dict[str, Any]:
    """Detach faces into a separate node."""
    rt = get_runtime()
    result, node = resolve_one(rt, node_name=node_name, handle=handle)
    if node is None:
        return result
    detached, warnings = detach_faces(
        rt,
        node,
        face_indices=face_indices,
        use_current_face_selection=use_current_face_selection,
        detach_name=detach_name,
    )
    if detached is None:
        return mesh_error("Could not detach faces", node=result.get("node"), warnings=warnings)
    return mesh_success(
        "Detached faces",
        source=topology_summary(rt, node),
        detached=topology_summary(rt, detached),
        warnings=warnings,
    )
