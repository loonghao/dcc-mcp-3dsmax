"""Set transform keyframes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._animation_utils import anim_success, resolve_anim_targets, set_transform_key
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    frame: float,
    property: str,  # noqa: A002
    value: list,
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
) -> Dict[str, Any]:
    """Set transform keyframes on explicit targets."""
    rt = get_runtime()
    targets = resolve_anim_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    changed = []
    for node in targets["objects"]:
        result = set_transform_key(rt, node, frame=frame, property_name=property, value=value)
        if not result.get("success"):
            return result
        changed.append(result["data"])
    return anim_success("Set transform keyframes", changes=changed, changed_key_count=len(changed))
