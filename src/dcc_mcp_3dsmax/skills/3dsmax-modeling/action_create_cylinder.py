"""Create a cylinder primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(radius: float = 30.0, height: float = 100.0, name: str = None) -> dict:
    """Create a cylinder with the given parameters.

    Returns
    -------
    dict
        The action response.
    """
    rt = get_runtime()
    cyl_obj = rt.Cylinder(radius=radius, height=height)

    if name:
        cyl_obj.name = name

    return {
        "success": True,
        "message": f"Created cylinder: {cyl_obj.name}",
        "data": {
            "node_name": str(cyl_obj.name),
            "object_id": int(cyl_obj.handle) if hasattr(cyl_obj, "handle") else None,
            "radius": radius,
            "height": height,
        },
    }
