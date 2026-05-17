"""Set a keyframe on an object in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Set a keyframe on the specified object.

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
    node_name = params.get("node_name")
    time = params.get("time")
    property_name = params.get("property", "position")
    value = params.get("value", None)

    if not node_name:
        return ActionResponse(
            success=False,
            message="node_name is required",
            data={},
        )

    if time is None:
        return ActionResponse(
            success=False,
            message="time (frame) is required",
            data={},
        )

    rt = get_runtime()

    # Get the node
    node = rt.getNodeByName(node_name)
    if node is None:
        return ActionResponse(
            success=False,
            message=f"Node not found: {node_name}",
            data={},
        )

    # Set keyframe based on property
    if property_name == "position":
        if value and len(value) >= 3:
            rt.animate(True)
            node.position = rt.point3(value[0], value[1], value[2])
            rt.setKey(node.position.controller, time)
            rt.animate(False)
    elif property_name == "rotation":
        if value and len(value) >= 3:
            rt.animate(True)
            node.rotation = rt.quat(value[0], value[1], value[2], value[3] if len(value) > 3 else 0)
            rt.setKey(node.rotation.controller, time)
            rt.animate(False)
    elif property_name == "scale":
        if value and len(value) >= 3:
            rt.animate(True)
            node.scale = rt.point3(value[0], value[1], value[2])
            rt.setKey(node.scale.controller, time)
            rt.animate(False)
    else:
        return ActionResponse(
            success=False,
            message=f"Unsupported property: {property_name}",
            data={},
        )

    return ActionResponse(
        success=True,
        message=f"Set keyframe on {node_name}.{property_name} at frame {time}",
        data={
            "node_name": node_name,
            "time": time,
            "property": property_name,
        },
    )
