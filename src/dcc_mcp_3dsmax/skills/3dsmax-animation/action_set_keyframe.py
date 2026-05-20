"""Set a keyframe on an object in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_name: str = None,
    time: int = None,
    property: str = "position",
    value: list = None,
) -> dict:
    """Set a keyframe on the specified object.

    Returns
    -------
    dict
        The action response.
    """
    if not node_name:
        return {"success": False, "message": "node_name is required", "data": {}}

    if time is None:
        return {"success": False, "message": "time (frame) is required", "data": {}}

    rt = get_runtime()

    # Get the node
    node = rt.getNodeByName(node_name)
    if node is None:
        return {"success": False, "message": f"Node not found: {node_name}", "data": {}}

    # Set keyframe based on property
    if property == "position":
        if value and len(value) >= 3:
            rt.animate(True)
            node.position = rt.point3(value[0], value[1], value[2])
            rt.setKey(node.position.controller, time)
            rt.animate(False)
    elif property == "rotation":
        if value and len(value) >= 3:
            rt.animate(True)
            node.rotation = rt.quat(value[0], value[1], value[2], value[3] if len(value) > 3 else 0)
            rt.setKey(node.rotation.controller, time)
            rt.animate(False)
    elif property == "scale":
        if value and len(value) >= 3:
            rt.animate(True)
            node.scale = rt.point3(value[0], value[1], value[2])
            rt.setKey(node.scale.controller, time)
            rt.animate(False)
    else:
        return {"success": False, "message": f"Unsupported property: {property}", "data": {}}

    return {
        "success": True,
        "message": f"Set keyframe on {node_name}.{property} at frame {time}",
        "data": {
            "node_name": node_name,
            "time": time,
            "property": property,
        },
    }
