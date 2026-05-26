"""Assign mesh smoothing groups."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import assign_smoothing_group, mesh_success, resolve_targets, smoothing_group_summary
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    smoothing_group: int,
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    face_indices: Optional[list] = None,
) -> Dict[str, Any]:
    """Assign a smoothing group to explicit targets."""
    rt = get_runtime()
    targets = resolve_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    warnings = []
    safe_group = max(1, min(int(smoothing_group), 32))
    for node in targets["objects"]:
        warnings.extend(assign_smoothing_group(rt, node, smoothing_group=safe_group, face_indices=face_indices))
    rows = [smoothing_group_summary(rt, node) for node in targets["objects"]]
    return mesh_success("Assigned smoothing group", nodes=rows, warnings=warnings)
