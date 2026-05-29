"""Create a plane primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import built-in modules
from typing import Any

# Import local modules
from dcc_mcp_3dsmax._scene_utils import set_node_position
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(width: float = 100.0, length: float = 100.0, name: str = None, position: Any = None) -> dict:
    """Create a plane with the given parameters.

    Returns
    -------
    dict
        The action response.
    """
    rt = get_runtime()
    plane_obj = rt.Plane(width=width, length=length)

    if name:
        plane_obj.name = name
    applied_position = set_node_position(rt, plane_obj, position)

    return {
        "success": True,
        "message": f"Created plane: {plane_obj.name}",
        "data": {
            "node_name": str(plane_obj.name),
            "object_id": int(plane_obj.handle) if hasattr(plane_obj, "handle") else None,
            "width": width,
            "length": length,
            "position": applied_position,
        },
    }
