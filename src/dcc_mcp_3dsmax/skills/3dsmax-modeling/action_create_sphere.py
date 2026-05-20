"""Create a sphere primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(radius: float = 50.0, name: str = None) -> dict:
    """Create a sphere with the given parameters.

    Returns
    -------
    dict
        The action response.
    """
    rt = get_runtime()
    sphere_obj = rt.Sphere(radius=radius)

    if name:
        sphere_obj.name = name

    return {
        "success": True,
        "message": f"Created sphere: {sphere_obj.name}",
        "data": {
            "node_name": str(sphere_obj.name),
            "object_id": int(sphere_obj.handle) if hasattr(sphere_obj, "handle") else None,
            "radius": radius,
        },
    }
