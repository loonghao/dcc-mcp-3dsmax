"""Create a cylinder primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Create a cylinder with the given parameters.

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
    radius = params.get("radius", 30.0)
    height = params.get("height", 100.0)
    name = params.get("name", None)

    rt = get_runtime()
    cyl_obj = rt.Cylinder(radius=radius, height=height)

    if name:
        cyl_obj.name = name

    return ActionResponse(
        success=True,
        message=f"Created cylinder: {cyl_obj.name}",
        data={
            "node_name": str(cyl_obj.name),
            "object_id": int(cyl_obj.handle) if hasattr(cyl_obj, "handle") else None,
            "radius": radius,
            "height": height,
        },
    )
