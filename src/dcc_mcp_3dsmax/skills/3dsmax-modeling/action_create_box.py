"""Create a box primitive in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Create a box with the given parameters.

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
    height = params.get("height", 100.0)
    depth = params.get("depth", 100.0)
    name = params.get("name", None)

    rt = get_runtime()
    box_obj = rt.Box(width=width, height=height, depth=depth)

    if name:
        box_obj.name = name

    return ActionResponse(
        success=True,
        message=f"Created box: {box_obj.name}",
        data={
            "node_name": str(box_obj.name),
            "object_id": int(box_obj.handle) if hasattr(box_obj, "handle") else None,
            "width": width,
            "height": height,
            "depth": depth,
        },
    )
