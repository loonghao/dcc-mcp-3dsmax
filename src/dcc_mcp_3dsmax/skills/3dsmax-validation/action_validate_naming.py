"""Validate node naming."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._validation_utils import resolve_validation_targets, response_for, validate_naming
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    pattern: str = r"^[A-Za-z][A-Za-z0-9_]*$",
    allow_spaces: bool = False,
) -> Dict[str, Any]:
    """Validate target node names."""
    rt = get_runtime()
    targets = resolve_validation_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    return response_for("naming", validate_naming(targets["objects"], pattern=pattern, allow_spaces=allow_spaces))
