"""Create a Standard material in 3ds Max."""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    name: str = "StandardMat",
    diffuse: list = None,
    specular: list = None,
    glossiness: float = 10.0,
) -> dict:
    """Create a Standard material with the given parameters.

    Returns
    -------
    dict
        The action response.
    """
    diffuse = diffuse or [255, 255, 255]
    specular = specular or [255, 255, 255]

    rt = get_runtime()

    # Create Standard material
    mat = rt.StandardMaterial(name=name)
    mat.diffuse = rt.color(diffuse[0], diffuse[1], diffuse[2])
    mat.specular = rt.color(specular[0], specular[1], specular[2])
    mat.glossiness = glossiness

    return {
        "success": True,
        "message": f"Created material: {name}",
        "data": {
            "material_name": name,
            "diffuse": diffuse,
            "specular": specular,
            "glossiness": glossiness,
        },
    }
