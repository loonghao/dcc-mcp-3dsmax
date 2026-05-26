"""Bake transform animation."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._animation_utils import anim_success, bake_transform_animation, resolve_anim_targets
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    start_frame: int,
    end_frame: int,
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    step: int = 1,
) -> Dict[str, Any]:
    """Bake transform animation samples."""
    rt = get_runtime()
    targets = resolve_anim_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    total = 0
    rows = []
    for node in targets["objects"]:
        result = bake_transform_animation(rt, node, start_frame=start_frame, end_frame=end_frame, step=step)
        if not result.get("success"):
            return result
        rows.append(result["data"])
        total += result["data"]["changed_key_count"]
    return anim_success("Baked transform animation", changes=rows, changed_key_count=total)
