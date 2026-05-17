"""Create a plane primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Create a plane with the given parameters.

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
    width = params.get("width", 100.0)
    length = params.get("length", 100.0)
    name = params.get("name", None)

    rt = get_runtime()
    plane_obj = rt.Plane(width=width, length=length)

    if name:
        plane_obj.name = name

    return ActionResponse(
        success=True,
        message=f"Created plane: {plane_obj.name}",
        data={
            "node_name": str(plane_obj.name),
            "object_id": int(plane_obj.handle) if hasattr(plane_obj, "handle") else None,
            "width": width,
            "length": length,
        },
    )
