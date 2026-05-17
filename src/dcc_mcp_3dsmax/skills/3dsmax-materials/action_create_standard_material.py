"""Create a Standard material in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Create a Standard material with the given parameters.

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
    name = params.get("name", "StandardMat")
    diffuse = params.get("diffuse", [255, 255, 255])
    specular = params.get("specular", [255, 255, 255])
    glossiness = params.get("glossiness", 10.0)

    rt = get_runtime()

    # Create Standard material
    mat = rt.StandardMaterial(name=name)
    mat.diffuse = rt.color(diffuse[0], diffuse[1], diffuse[2])
    mat.specular = rt.color(specular[0], specular[1], specular[2])
    mat.glossiness = glossiness

    return ActionResponse(
        success=True,
        message=f"Created material: {name}",
        data={
            "material_name": name,
            "diffuse": diffuse,
            "specular": specular,
            "glossiness": glossiness,
        },
    )
