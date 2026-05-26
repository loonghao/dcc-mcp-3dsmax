"""Apply a deformer modifier."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._rigging_utils import apply_deformer, resolve_rig_targets, rig_success
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    deformer_type: str,
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    attributes: Optional[dict] = None,
) -> Dict[str, Any]:
    """Apply a common deformer modifier to explicit targets."""
    rt = get_runtime()
    targets = resolve_rig_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    changes = []
    total = 0
    for node in targets["objects"]:
        result = apply_deformer(rt, node, deformer_type=deformer_type, attributes=attributes)
        if not result.get("success"):
            return result
        changes.append(result["data"])
        total += result["data"]["changed_modifier_count"]
    return rig_success("Applied deformer modifiers", changes=changes, changed_modifier_count=total)
