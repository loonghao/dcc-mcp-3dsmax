"""Create PBR-friendly materials."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._material_utils import create_material, material_identity, material_success, set_material_attribute
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    name: str,
    base_color: Optional[list] = None,
    roughness: Optional[float] = None,
    metalness: Optional[float] = None,
) -> Dict[str, Any]:
    """Create a PBR-friendly material."""
    material = create_material(get_runtime(), name=name, kind="pbr", color=base_color)
    warnings = []
    for attr, value in (("roughness", roughness), ("metalness", metalness)):
        if value is not None:
            warnings.extend(set_material_attribute(material, attr, value))
    return material_success("Created PBR material", material=material_identity(material), warnings=warnings)
