"""Create a box primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(width: float = 100.0, height: float = 100.0, depth: float = 100.0, name: str = None) -> dict:
    """Create a box with the given parameters.

    Returns
    -------
    dict
        The action response.
    """
    rt = get_runtime()
    box_obj = rt.Box(width=width, height=height, depth=depth)

    if name:
        box_obj.name = name

    return {
        "success": True,
        "message": f"Created box: {box_obj.name}",
        "data": {
            "node_name": str(box_obj.name),
            "object_id": int(box_obj.handle) if hasattr(box_obj, "handle") else None,
            "width": width,
            "height": height,
            "depth": depth,
        },
    }
