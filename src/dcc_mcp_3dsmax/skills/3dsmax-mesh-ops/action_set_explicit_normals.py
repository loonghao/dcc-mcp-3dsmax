"""Set explicit normals on mesh targets."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import changed_summary, mesh_success, resolve_targets, set_explicit_normals
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    normal: list,
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
) -> Dict[str, Any]:
    """Set explicit normals on explicit mesh targets."""
    rt = get_runtime()
    targets = resolve_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    warnings = []
    for node in targets["objects"]:
        warnings.extend(set_explicit_normals(rt, node, normal))
    return mesh_success("Set explicit normals", nodes=changed_summary(rt, targets["objects"]), warnings=warnings)
