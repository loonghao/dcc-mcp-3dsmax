"""Run mesh cleanup checks."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import changed_summary, cleanup_node, mesh_success, resolve_targets
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    weld_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """Run cleanup operations on explicit mesh targets."""
    rt = get_runtime()
    targets = resolve_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    warnings = []
    for node in targets["objects"]:
        warnings.extend(cleanup_node(rt, node, weld_threshold=weld_threshold))
    return mesh_success("Cleaned meshes", nodes=changed_summary(rt, targets["objects"]), warnings=warnings)
