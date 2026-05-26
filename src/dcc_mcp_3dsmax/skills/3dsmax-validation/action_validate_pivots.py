"""Validate pivots."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._validation_utils import resolve_validation_targets, response_for, validate_pivots
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    mode: str = "bounds_center",
    tolerance: float = 0.001,
) -> Dict[str, Any]:
    """Validate pivot placement."""
    rt = get_runtime()
    targets = resolve_validation_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    return response_for("pivots", validate_pivots(targets["objects"], mode=mode, tolerance=tolerance))
