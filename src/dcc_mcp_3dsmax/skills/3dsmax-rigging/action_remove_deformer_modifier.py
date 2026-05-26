"""Remove deformer modifiers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._rigging_utils import remove_deformer, resolve_rig_targets, rig_success
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    deformer_type: Optional[str] = None,
    modifier_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Remove matching deformer modifiers from explicit targets."""
    rt = get_runtime()
    targets = resolve_rig_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    changes = []
    total = 0
    for node in targets["objects"]:
        result = remove_deformer(node, deformer_type=deformer_type, modifier_name=modifier_name)
        if not result.get("success"):
            return result
        changes.append(result["data"])
        total += result["data"]["changed_modifier_count"]
    return rig_success("Removed deformer modifiers", changes=changes, changed_modifier_count=total)
