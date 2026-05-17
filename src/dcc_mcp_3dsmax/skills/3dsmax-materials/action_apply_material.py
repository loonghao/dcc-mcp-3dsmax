"""Apply a material to objects in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Apply a material to specified objects or selection.

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
    material_name = params.get("material_name")
    node_names = params.get("node_names", None)

    if not material_name:
        return ActionResponse(
            success=False,
            message="material_name is required",
            data={},
        )

    rt = get_runtime()

    # Get the material
    mat = rt.getNodeByName(material_name)
    if mat is None:
        # Try to find in scene materials
        for m in rt.scenematerials:
            if str(m.name) == material_name:
                mat = m
                break

    if mat is None:
        return ActionResponse(
            success=False,
            message=f"Material not found: {material_name}",
            data={},
        )

    # Get target nodes
    if node_names:
        nodes = [rt.getNodeByName(n) for n in node_names]
        nodes = [n for n in nodes if n is not None]
    else:
        # Use current selection
        nodes = list(rt.selection)

    if not nodes:
        return ActionResponse(
            success=False,
            message="No nodes to apply material to",
            data={},
        )

    # Apply material
    applied_count = 0
    for node in nodes:
        node.material = mat
        applied_count += 1

    return ActionResponse(
        success=True,
        message=f"Applied material '{material_name}' to {applied_count} node(s)",
        data={
            "material_name": material_name,
            "applied_count": applied_count,
        },
    )
