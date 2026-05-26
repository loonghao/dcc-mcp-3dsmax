"""Copy UV channels."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._uv_atlas import changed_channels, copy_channel, resolve_uv_targets, uv_success, validate_channel
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    source_channel: int,
    target_channel: int,
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
) -> Dict[str, Any]:
    """Copy one UV channel to another on explicit targets."""
    for channel in (source_channel, target_channel):
        error = validate_channel(channel)
        if error is not None:
            return error
    rt = get_runtime()
    targets = resolve_uv_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    warnings = []
    for node in targets["objects"]:
        warnings.extend(copy_channel(rt, node, int(source_channel), int(target_channel)))
    return uv_success("Copied UV channel", nodes=changed_channels(rt, targets["objects"]), warnings=warnings)
