"""Set a constraint target."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._rigging_utils import set_constraint_target
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    constraint_type: str,
    constrained_name: Optional[str] = None,
    constrained_handle: Optional[int] = None,
    target_name: Optional[str] = None,
    target_handle: Optional[int] = None,
    weight: float = 100.0,
) -> Dict[str, Any]:
    """Create or update a basic transform constraint target."""
    return set_constraint_target(
        get_runtime(),
        constrained_name=constrained_name,
        constrained_handle=constrained_handle,
        target_name=target_name,
        target_handle=target_handle,
        constraint_type=constraint_type,
        weight=weight,
    )
