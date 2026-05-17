"""Create a sphere primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Create a sphere with the given parameters.

    Parameters
    ----------
    request : ActionRequest
        The action request containing parameters.

    Returns
    -------
    ActionResponse
        The action response.
    """
    params = request.params or {}
    radius = params.get("radius", 50.0)
    name = params.get("name", None)

    rt = get_runtime()
    sphere_obj = rt.Sphere(radius=radius)

    if name:
        sphere_obj.name = name

    return ActionResponse(
        success=True,
        message=f"Created sphere: {sphere_obj.name}",
        data={
            "node_name": str(sphere_obj.name),
            "object_id": int(sphere_obj.handle) if hasattr(sphere_obj, "handle") else None,
            "radius": radius,
        },
    )
