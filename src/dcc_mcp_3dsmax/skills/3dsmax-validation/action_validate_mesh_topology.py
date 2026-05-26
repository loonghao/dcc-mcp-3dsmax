"""Validate mesh topology."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._validation_utils import resolve_validation_targets, response_for, validate_mesh_topology
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    max_open_edges: int = 0,
    max_isolated_vertices: int = 0,
    max_ngons: int = 0,
) -> Dict[str, Any]:
    """Validate mesh topology counts."""
    rt = get_runtime()
    targets = resolve_validation_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    return response_for(
        "mesh_topology",
        validate_mesh_topology(
            targets["objects"],
            max_open_edges=max_open_edges,
            max_isolated_vertices=max_isolated_vertices,
            max_ngons=max_ngons,
        ),
    )
