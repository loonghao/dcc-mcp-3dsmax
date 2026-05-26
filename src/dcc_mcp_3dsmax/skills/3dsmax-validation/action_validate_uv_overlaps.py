"""Validate UV overlaps."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._validation_utils import resolve_validation_targets, response_for, validate_uv_overlaps
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    max_overlap_count: int = 0,
) -> Dict[str, Any]:
    """Validate UV overlap counts."""
    rt = get_runtime()
    targets = resolve_validation_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    return response_for("uv_overlaps", validate_uv_overlaps(targets["objects"], max_overlap_count=max_overlap_count))
