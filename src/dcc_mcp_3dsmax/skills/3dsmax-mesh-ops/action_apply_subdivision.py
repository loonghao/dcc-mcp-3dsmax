"""Apply subdivision modifiers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import apply_subdivision, changed_summary, mesh_success, resolve_targets
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    iterations: int = 1,
    render_iterations: Optional[int] = None,
) -> Dict[str, Any]:
    """Apply subdivision to explicit mesh targets."""
    rt = get_runtime()
    targets = resolve_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    warnings = []
    safe_iterations = max(0, min(int(iterations), 6))
    safe_render = None if render_iterations is None else max(0, min(int(render_iterations), 6))
    for node in targets["objects"]:
        warnings.extend(apply_subdivision(rt, node, safe_iterations, safe_render))
    return mesh_success("Applied subdivision", nodes=changed_summary(rt, targets["objects"]), warnings=warnings)
