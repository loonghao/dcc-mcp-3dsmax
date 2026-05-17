"""Get 3ds Max scene information."""

# Import future modules
from __future__ import annotations

# Import built-in modules
from typing import Any, Dict

# Import local modules
from dcc_mcp_3dsmax.api import max_success, with_max


@with_max
def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get basic information about the current scene.

    Args:
        params: Dictionary with no required parameters.

    Returns:
        Dictionary with scene information.
    """
    import pymxs

    rt = pymxs.runtime

    # Get scene name
    scene_name = rt.maxFileName if rt.maxFileName else "Untitled"

    # Get node count
    all_nodes = rt.objects
    node_count = len(list(all_nodes))

    # Get units
    units = str(rt.units.SystemType()) if hasattr(rt.units, "SystemType") else "unknown"

    return max_success(
        "Retrieved scene information",
        scene_name=scene_name,
        node_count=node_count,
        units=units,
    )
