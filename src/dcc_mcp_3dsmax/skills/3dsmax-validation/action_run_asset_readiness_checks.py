"""Run aggregate asset-readiness validation."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._validation_utils import resolve_validation_targets, run_validators
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    validators: Optional[list] = None,
    required_uv_channels: Optional[list] = None,
    naming_pattern: str = r"^[A-Za-z][A-Za-z0-9_]*$",
) -> Dict[str, Any]:
    """Run selected validators and aggregate the report."""
    rt = get_runtime()
    targets = resolve_validation_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    return run_validators(
        targets["objects"],
        validators=validators,
        required_uv_channels=required_uv_channels,
        naming_pattern=naming_pattern,
    )
