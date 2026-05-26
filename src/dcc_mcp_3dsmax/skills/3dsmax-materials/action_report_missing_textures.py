"""Report missing material texture paths."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._material_utils import (
    find_material,
    iter_scene_materials,
    material_error,
    material_success,
    missing_textures,
)
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(material_names: Optional[list] = None) -> Dict[str, Any]:
    """Report missing bitmap texture paths."""
    rt = get_runtime()
    if material_names:
        materials = []
        for name in material_names:
            material = find_material(rt, str(name))
            if material is None:
                return material_error("Material not found", material_name=str(name))
            materials.append(material)
    else:
        materials = iter_scene_materials(rt)
    missing = missing_textures(materials)
    return material_success("Reported missing textures", missing_textures=missing, count=len(missing))
